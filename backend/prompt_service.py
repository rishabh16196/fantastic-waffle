"""
Prompt Management Service

Handles fetching, rendering, and seeding of AI prompts from the database.
Supports Jinja2 templating for dynamic variable substitution.
"""

from typing import Dict, Any, Optional
from jinja2 import Template, Environment, BaseLoader
from sqlalchemy.orm import Session
from models import Prompt
from prompts import load_default_prompts


# Jinja2 environment for rendering templates
jinja_env = Environment(loader=BaseLoader())


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
    ).order_by(Prompt.version.desc()).first()


def set_prompt_active(db: Session, prompt_id: str) -> Optional[Prompt]:
    """
    Set a specific prompt version as active and deactivate others with the same key.
    """
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        return None

    db.query(Prompt).filter(
        Prompt.key == prompt.key,
        Prompt.is_active == True,
        Prompt.id != prompt_id
    ).update({"is_active": False})

    prompt.is_active = True
    db.commit()
    db.refresh(prompt)
    return prompt


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
    default_prompts = load_default_prompts()
    
    for prompt_data in default_prompts:
        existing = db.query(Prompt).filter(Prompt.key == prompt_data["key"]).first()
        if not existing:
            prompt = Prompt(
                key=prompt_data["key"],
                name=prompt_data["name"],
                description=prompt_data["description"],
                system_message=prompt_data["system_message"],
                user_message_template=prompt_data["user_message_template"],
                model=prompt_data["model"],
                temperature=prompt_data["temperature"],
                version=1,
                is_active=True
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
    return db.query(Prompt).order_by(Prompt.key.asc(), Prompt.version.desc()).all()


def update_prompt(
    db: Session,
    key: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_message: Optional[str] = None,
    user_message_template: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[str] = None,
    is_active: Optional[bool] = None
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
    current_prompt = get_prompt(db, key)
    if not current_prompt:
        return None

    latest_version = db.query(Prompt).filter(Prompt.key == key).order_by(Prompt.version.desc()).first()
    next_version = (latest_version.version if latest_version else 0) + 1

    new_prompt = Prompt(
        key=key,
        name=name if name is not None else current_prompt.name,
        description=description if description is not None else current_prompt.description,
        system_message=system_message if system_message is not None else current_prompt.system_message,
        user_message_template=user_message_template if user_message_template is not None else current_prompt.user_message_template,
        model=model if model is not None else current_prompt.model,
        temperature=temperature if temperature is not None else current_prompt.temperature,
        version=next_version,
        is_active=True if is_active is None else is_active
    )
    db.add(new_prompt)

    if new_prompt.is_active:
        db.query(Prompt).filter(
            Prompt.key == key,
            Prompt.is_active == True
        ).update({"is_active": False})

    new_prompt.is_active = True if new_prompt.is_active else False
    db.commit()
    db.refresh(new_prompt)
    return new_prompt
