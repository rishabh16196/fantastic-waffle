"""
SQLAlchemy ORM models for the Leveling Guide Generator.

Data Model Design (Normalized):
- Company: An organization using the platform
- User: A manager or employee belonging to a company
- Role: A job role within a company (e.g., Software Engineer, Product Manager)
- Level: A seniority level for a role (e.g., L1, L2, L3)
- Competency: A skill area for a role (e.g., Technical Skills, Leadership)
- Definition: The requirement text at the intersection of level + competency
- Example: AI-generated examples for a definition
- Nudge: An employee request for a missing leveling guide

This normalized structure enables:
- Querying all examples for a specific role/level
- Querying all examples for a competency across levels
- Company-scoped data isolation
- Persistent storage without session tracking
"""

import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


def generate_invite_code():
    """Generate a short, readable invite code."""
    return secrets.token_urlsafe(6).upper()[:8]


class Company(Base):
    """
    An organization using the platform.
    Managers create companies, employees join via invite code.
    """
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    domain = Column(String(200), nullable=True)
    invite_code = Column(String(20), unique=True, default=generate_invite_code)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="company", cascade="all, delete-orphan")
    levels = relationship("Level", back_populates="company", cascade="all, delete-orphan")
    competencies = relationship("Competency", back_populates="company", cascade="all, delete-orphan")
    definitions = relationship("Definition", back_populates="company", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="company", cascade="all, delete-orphan")
    nudges = relationship("Nudge", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    """
    A user (manager or employee) belonging to a company.
    Simple auth: just email + company association, no passwords.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)  # "manager" or "employee"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="users")
    nudges = relationship("Nudge", back_populates="employee")


class Role(Base):
    """
    A job role within a company (e.g., Software Engineer, Product Manager).
    Each role has its own levels and competencies.
    """
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="roles")
    levels = relationship("Level", back_populates="role", cascade="all, delete-orphan")
    competencies = relationship("Competency", back_populates="role", cascade="all, delete-orphan")
    definitions = relationship("Definition", back_populates="role", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="role", cascade="all, delete-orphan")


class Level(Base):
    """
    A seniority level for a role (e.g., L1 - Junior, L2 - Mid, L3 - Senior).
    """
    __tablename__ = "levels"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    name = Column(String(200), nullable=False)
    order_idx = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="levels")
    role = relationship("Role", back_populates="levels")
    definitions = relationship("Definition", back_populates="level", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="level", cascade="all, delete-orphan")


class Competency(Base):
    """
    A skill area for a role (e.g., Technical Skills, Leadership, Communication).
    """
    __tablename__ = "competencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    name = Column(String(200), nullable=False)
    order_idx = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="competencies")
    role = relationship("Role", back_populates="competencies")
    definitions = relationship("Definition", back_populates="competency", cascade="all, delete-orphan")
    examples = relationship("Example", back_populates="competency", cascade="all, delete-orphan")


class Definition(Base):
    """
    The requirement text at the intersection of a level and competency.
    This is the original text from the leveling guide.
    """
    __tablename__ = "definitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    level_id = Column(String(36), ForeignKey("levels.id"), nullable=False)
    competency_id = Column(String(36), ForeignKey("competencies.id"), nullable=False)
    definition = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="definitions")
    role = relationship("Role", back_populates="definitions")
    level = relationship("Level", back_populates="definitions")
    competency = relationship("Competency", back_populates="definitions")


class Example(Base):
    """
    An AI-generated example for a specific role/level/competency combination.
    Multiple examples can exist per combination.
    """
    __tablename__ = "examples"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    level_id = Column(String(36), ForeignKey("levels.id"), nullable=False)
    competency_id = Column(String(36), ForeignKey("competencies.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="examples")
    role = relationship("Role", back_populates="examples")
    level = relationship("Level", back_populates="examples")
    competency = relationship("Competency", back_populates="examples")


class Nudge(Base):
    """
    An employee request for a missing leveling guide.
    Employees can nudge managers to create guides for specific roles/levels.
    """
    __tablename__ = "nudges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_name = Column(String(200), nullable=False)
    level_name = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")  # pending, fulfilled, dismissed
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="nudges")
    employee = relationship("User", back_populates="nudges")


class Prompt(Base):
    """
    Stores AI prompts with Jinja2 templating support.
    Allows runtime editing of prompts without code changes.
    
    Available template variables:
    - parse_guide: {{raw_text}}
    - generate_examples: {{company_url}}, {{role_name}}, {{level_name}}, 
                         {{competency_name}}, {{requirement}}
    """
    __tablename__ = "prompts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(100), unique=True, nullable=False)  # e.g., "parse_guide", "generate_examples"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    system_message = Column(Text, nullable=False)  # System role content
    user_message_template = Column(Text, nullable=False)  # Jinja2 template
    model = Column(String(50), default="gpt-4o")
    temperature = Column(String(10), default="0.7")  # Stored as string to avoid float precision issues
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
