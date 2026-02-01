"""
OpenAI service for parsing leveling guides and generating examples.

Features:
1. parse_leveling_guide: Extract structured data from raw text
2. generate_examples: Create specific examples for each cell
3. process_and_save_leveling_guide: Complete flow with BATCHED PARALLEL processing
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from sqlalchemy.orm import Session as DBSession
from schemas import ParsedLevelingGuide, ParsedCell
from models import Role, Level, Competency, Definition, Example

# Configuration
BATCH_SIZE = 10  # Number of parallel API calls per batch
MAX_WORKERS = 10  # Max threads for parallel processing

# Lazy client initialization to avoid errors on import
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your-key-here":
            raise ValueError("Please set a valid OPENAI_API_KEY in your .env file")
        _client = OpenAI(api_key=api_key)
    return _client


def parse_leveling_guide(raw_text: str) -> ParsedLevelingGuide:
    """
    Parse raw text from a leveling guide into structured format.
    
    Uses GPT-4 to understand the table structure and extract:
    - Level names (rows)
    - Competency names (columns)
    - Cell contents (requirements at each level/competency intersection)
    """
    
    prompt = """You are parsing a leveling guide document. Extract the structure into JSON format.

A leveling guide is a table where:
- Rows represent career levels (e.g., L1-Junior, L2-Mid, L3-Senior, etc.)
- Columns represent competencies/skills (e.g., Technical Skills, Leadership, Communication, etc.)
- Each cell describes what's expected at that level for that competency

Extract and return a JSON object with this exact structure:
{
    "levels": ["Level 1 Name", "Level 2 Name", ...],
    "competencies": ["Competency 1 Name", "Competency 2 Name", ...],
    "cells": [
        {"level_name": "Level 1 Name", "competency_name": "Competency 1 Name", "requirement": "Description text..."},
        ...
    ]
}

Rules:
- Preserve the exact level and competency names from the document
- Keep levels in order from junior to senior
- Keep competencies in their original order
- Include ALL cells from the table
- The requirement should be the full text from that cell

Here is the leveling guide text to parse:

"""

    response = get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that parses leveling guides into structured JSON. Always respond with valid JSON only, no markdown formatting."},
            {"role": "user", "content": prompt + raw_text}
        ],
        temperature=0.1,  # Low temperature for consistent parsing
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Convert to Pydantic model
    cells = [ParsedCell(**cell) for cell in result.get("cells", [])]
    return ParsedLevelingGuide(
        levels=result.get("levels", []),
        competencies=result.get("competencies", []),
        cells=cells
    )


def generate_examples_for_cell(
    company_url: str,
    role_name: str,
    level_name: str,
    competency_name: str,
    requirement: str
) -> List[str]:
    """
    Generate 3 specific examples for a single cell in the leveling guide.
    
    Args:
        company_url: The company's website (for context)
        role_name: The role being leveled (e.g., "Software Engineer")
        level_name: The level (e.g., "L3 - Senior")
        competency_name: The competency (e.g., "Technical Skills")
        requirement: The requirement text from the leveling guide
    
    Returns:
        List of 3 example strings
    """
    
    prompt = f"""You are helping a manager explain career expectations to their direct reports.

Context:
- Company: {company_url}
- Role: {role_name}
- Level: {level_name}
- Competency Area: {competency_name}

The leveling guide says someone at this level should demonstrate:
"{requirement}"

Generate exactly 3 SPECIFIC, ACTIONABLE examples of what an employee could DO to demonstrate they are operating at this level. 

Each example should:
1. Be concrete and observable (not vague like "show leadership")
2. Be realistic for the role and level
3. Include enough detail that an employee knows exactly what to do
4. Be different from the other examples (cover different scenarios)

Format your response as a JSON object:
{{"examples": ["Example 1 text", "Example 2 text", "Example 3 text"]}}
"""

    response = get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a career coach helping employees understand what great performance looks like. Give specific, actionable examples. Respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,  # Some creativity for varied examples
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result.get("examples", [])[:3]  # Ensure max 3 examples


def _generate_examples_task(
    cell_key: str,
    company_url: str,
    role_name: str,
    level_name: str,
    competency_name: str,
    requirement: str
) -> Tuple[str, List[str]]:
    """
    Wrapper for parallel execution. Returns (cell_key, examples).
    """
    try:
        examples = generate_examples_for_cell(
            company_url=company_url,
            role_name=role_name,
            level_name=level_name,
            competency_name=competency_name,
            requirement=requirement
        )
        return (cell_key, examples)
    except Exception as e:
        print(f"Error generating examples for {level_name}/{competency_name}: {e}")
        return (cell_key, [])


def process_and_save_leveling_guide(
    db: DBSession,
    company_id: str,
    role_name: str,
    company_url: str,
    raw_text: str
) -> Role:
    """
    Complete processing flow: parse guide, create role structure, generate examples, save to DB.
    
    Uses BATCHED PARALLEL processing for example generation to speed up the process.
    
    Args:
        db: Database session
        company_id: ID of the company
        role_name: Name of the role (e.g., "Software Engineer")
        company_url: Company website for context
        raw_text: Raw text content from uploaded file
    
    Returns:
        The created Role object with all relationships populated
    """
    
    # Step 1: Parse the leveling guide
    print(f"[1/4] Parsing leveling guide for {role_name}...")
    parsed_guide = parse_leveling_guide(raw_text)
    print(f"      Found {len(parsed_guide.levels)} levels, {len(parsed_guide.competencies)} competencies, {len(parsed_guide.cells)} cells")
    
    # Step 2: Create or update the role
    print(f"[2/4] Setting up role in database...")
    existing_role = db.query(Role).filter(
        Role.company_id == company_id,
        Role.name == role_name,
        Role.is_active == True
    ).first()
    
    if existing_role:
        # Soft delete old data by marking inactive
        existing_role.is_active = False
        db.flush()
    
    # Create new role
    role = Role(
        company_id=company_id,
        name=role_name
    )
    db.add(role)
    db.flush()
    
    # Step 3: Create levels and competencies
    level_map: Dict[str, Level] = {}
    for idx, level_name in enumerate(parsed_guide.levels):
        level = Level(
            company_id=company_id,
            role_id=role.id,
            name=level_name,
            order_idx=idx
        )
        db.add(level)
        db.flush()
        level_map[level_name] = level
    
    competency_map: Dict[str, Competency] = {}
    for idx, competency_name in enumerate(parsed_guide.competencies):
        competency = Competency(
            company_id=company_id,
            role_id=role.id,
            name=competency_name,
            order_idx=idx
        )
        db.add(competency)
        db.flush()
        competency_map[competency_name] = competency
    
    # Step 4: Create definitions first (without examples)
    print(f"[3/4] Creating definitions...")
    cell_definitions: Dict[str, Definition] = {}
    for cell in parsed_guide.cells:
        level = level_map.get(cell.level_name)
        competency = competency_map.get(cell.competency_name)
        
        if not level or not competency:
            continue
        
        definition = Definition(
            company_id=company_id,
            role_id=role.id,
            level_id=level.id,
            competency_id=competency.id,
            definition=cell.requirement
        )
        db.add(definition)
        db.flush()
        
        cell_key = f"{cell.level_name}|{cell.competency_name}"
        cell_definitions[cell_key] = definition
    
    # Step 5: Generate examples in BATCHED PARALLEL
    print(f"[4/4] Generating examples in parallel (batch size: {BATCH_SIZE})...")
    
    # Prepare all tasks
    tasks = []
    for cell in parsed_guide.cells:
        level = level_map.get(cell.level_name)
        competency = competency_map.get(cell.competency_name)
        if not level or not competency:
            continue
        
        cell_key = f"{cell.level_name}|{cell.competency_name}"
        tasks.append({
            "cell_key": cell_key,
            "company_url": company_url,
            "role_name": role_name,
            "level_name": cell.level_name,
            "competency_name": cell.competency_name,
            "requirement": cell.requirement,
            "level_id": level.id,
            "competency_id": competency.id
        })
    
    # Process in batches
    total_batches = (len(tasks) + BATCH_SIZE - 1) // BATCH_SIZE
    all_results: Dict[str, List[str]] = {}
    
    for batch_idx in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        print(f"      Processing batch {batch_num}/{total_batches} ({len(batch)} cells)...")
        
        # Run batch in parallel
        with ThreadPoolExecutor(max_workers=min(len(batch), MAX_WORKERS)) as executor:
            futures = {
                executor.submit(
                    _generate_examples_task,
                    task["cell_key"],
                    task["company_url"],
                    task["role_name"],
                    task["level_name"],
                    task["competency_name"],
                    task["requirement"]
                ): task
                for task in batch
            }
            
            for future in as_completed(futures):
                task = futures[future]
                try:
                    cell_key, examples = future.result()
                    all_results[cell_key] = examples
                except Exception as e:
                    print(f"      Error in batch for {task['level_name']}/{task['competency_name']}: {e}")
                    all_results[task["cell_key"]] = []
    
    # Save all examples to database
    print(f"      Saving {sum(len(ex) for ex in all_results.values())} examples to database...")
    for task in tasks:
        cell_key = task["cell_key"]
        examples = all_results.get(cell_key, [])
        
        for example_content in examples:
            example = Example(
                company_id=company_id,
                role_id=role.id,
                level_id=task["level_id"],
                competency_id=task["competency_id"],
                content=example_content
            )
            db.add(example)
    
    db.commit()
    db.refresh(role)
    
    print(f"      Done! Role '{role_name}' created with {len(all_results)} definitions and examples.")
    
    return role
