"""
Prompt Management Service

Handles fetching, rendering, and seeding of AI prompts from the database.
Supports Jinja2 templating for dynamic variable substitution.
"""

from typing import Dict, Any, Optional
from jinja2 import Template, Environment, BaseLoader
from sqlalchemy.orm import Session
from models import Prompt


# Jinja2 environment for rendering templates
jinja_env = Environment(loader=BaseLoader())


# ==================== DEFAULT PROMPTS ====================
# These are seeded on first startup if no prompts exist

DEFAULT_PROMPTS = [
    {
        "key": "parse_guide",
        "name": "Parse Leveling Guide",
        "description": "Parses raw PDF text into structured levels, competencies, and requirements.",
        "system_message": "You are a helpful assistant that parses leveling guides into structured JSON. Always respond with valid JSON only, no markdown formatting.",
        "user_message_template": """You are parsing a leveling guide document. Extract the structure into JSON format.

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

{{raw_text}}""",
        "model": "gpt-4o",
        "temperature": "0.1"
    },
    {
        "key": "generate_examples",
        "name": "Generate Examples",
        "description": "Generates 3 specific, actionable examples for a leveling guide cell.",
        "system_message": "You are a career coach helping employees understand what great performance looks like. Give specific, actionable examples. Respond with valid JSON only.",
        "user_message_template": """You are helping a manager explain career expectations to their direct reports.

Context:
- Company: {{company_url}}
- Role: {{role_name}}
- Level: {{level_name}}
- Competency Area: {{competency_name}}

The leveling guide says someone at this level should demonstrate:
"{{requirement}}"

Generate exactly 3 SPECIFIC, ACTIONABLE examples of what an employee could DO to demonstrate they are operating at this level. 

Each example should:
1. Be concrete and observable (not vague like "show leadership")
2. Be realistic for the role and level
3. Include enough detail that an employee knows exactly what to do
4. Be different from the other examples (cover different scenarios)

Format your response as a JSON object:
{"examples": ["Example 1 text", "Example 2 text", "Example 3 text"]}""",
        "model": "gpt-4o",
        "temperature": "0.7"
    }
]


def get_prompt(db: Session, key: str) -> Optional[Prompt]:
    """
    Fetch a prompt by its unique key.
    
    Args:
        db: Database session
        key: Unique prompt identifier (e.g., "parse_guide", "generate_examples")
    
    Returns:
        Prompt object or None if not found
    """
    return db.query(Prompt).filter(
        Prompt.key == key,
        Prompt.is_active == True
    ).first()


def render_prompt(template_str: str, variables: Dict[str, Any]) -> str:
    """
    Render a Jinja2 template with provided variables.
    
    Args:
        template_str: Jinja2 template string
        variables: Dictionary of template variables
    
    Returns:
        Rendered string
    """
    template = jinja_env.from_string(template_str)
    return template.render(**variables)


def get_rendered_prompt(db: Session, key: str, variables: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a prompt and render its user message template with variables.
    
    Args:
        db: Database session
        key: Unique prompt identifier
        variables: Dictionary of template variables (default: empty)
    
    Returns:
        Dictionary with rendered prompt data or None if prompt not found
        {
            "system_message": str,
            "user_message": str,
            "model": str,
            "temperature": float
        }
    """
    prompt = get_prompt(db, key)
    if not prompt:
        return None
    
    variables = variables or {}
    user_message = render_prompt(prompt.user_message_template, variables)
    
    return {
        "system_message": prompt.system_message,
        "user_message": user_message,
        "model": prompt.model,
        "temperature": float(prompt.temperature)
    }


def seed_default_prompts(db: Session) -> int:
    """
    Seed default prompts if they don't exist.
    Called on application startup.
    
    Args:
        db: Database session
    
    Returns:
        Number of prompts created
    """
    created_count = 0
    
    for prompt_data in DEFAULT_PROMPTS:
        existing = db.query(Prompt).filter(Prompt.key == prompt_data["key"]).first()
        if not existing:
            prompt = Prompt(
                key=prompt_data["key"],
                name=prompt_data["name"],
                description=prompt_data["description"],
                system_message=prompt_data["system_message"],
                user_message_template=prompt_data["user_message_template"],
                model=prompt_data["model"],
                temperature=prompt_data["temperature"]
            )
            db.add(prompt)
            created_count += 1
    
    if created_count > 0:
        db.commit()
    
    return created_count


def list_prompts(db: Session) -> list:
    """
    List all active prompts.
    
    Args:
        db: Database session
    
    Returns:
        List of Prompt objects
    """
    return db.query(Prompt).filter(Prompt.is_active == True).all()


def update_prompt(
    db: Session,
    key: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_message: Optional[str] = None,
    user_message_template: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[str] = None
) -> Optional[Prompt]:
    """
    Update an existing prompt.
    
    Args:
        db: Database session
        key: Unique prompt identifier
        **kwargs: Fields to update
    
    Returns:
        Updated Prompt object or None if not found
    """
    prompt = get_prompt(db, key)
    if not prompt:
        return None
    
    if name is not None:
        prompt.name = name
    if description is not None:
        prompt.description = description
    if system_message is not None:
        prompt.system_message = system_message
    if user_message_template is not None:
        prompt.user_message_template = user_message_template
    if model is not None:
        prompt.model = model
    if temperature is not None:
        prompt.temperature = temperature
    
    db.commit()
    db.refresh(prompt)
    return prompt
