"""
Prompts Package

Provides default AI prompts for the Leveling Guide Generator.
Prompts are stored in defaults.yaml and loaded on application startup.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any


def load_default_prompts() -> List[Dict[str, Any]]:
    """
    Load default prompts from the YAML file.
    
    Returns:
        List of prompt dictionaries with keys:
        - key: Unique identifier (e.g., "parse_guide", "generate_examples")
        - name: Human-readable name
        - description: What the prompt does
        - model: OpenAI model to use
        - temperature: Model temperature (as string)
        - system_message: System role content
        - user_message_template: Jinja2 template for user message
    """
    yaml_path = Path(__file__).parent / "defaults.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
