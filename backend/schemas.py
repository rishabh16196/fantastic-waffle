"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# === Auth Request Schemas ===

class ManagerRegisterRequest(BaseModel):
    """Manager creates a new company and account."""
    email: str
    name: str
    company_name: str
    company_domain: Optional[str] = None


class EmployeeJoinRequest(BaseModel):
    """Employee joins an existing company via invite code."""
    email: str
    name: str
    invite_code: str


class LoginRequest(BaseModel):
    """Login with email (simple auth - no password)."""
    email: str


# === Auth Response Schemas ===

class CompanyResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    invite_code: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    company_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response after successful auth (register/join)."""
    user: UserResponse
    company: CompanyResponse


class MeResponse(BaseModel):
    """Current user info with company details."""
    user: UserResponse
    company: CompanyResponse


# === Nudge Schemas ===

class NudgeCreateRequest(BaseModel):
    """Employee requests a leveling guide."""
    role_name: str
    level_name: Optional[str] = None


class NudgeResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    role_name: str
    level_name: Optional[str] = None
    status: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    employee_name: Optional[str] = None  # Populated in API

    class Config:
        from_attributes = True


class NudgeUpdateRequest(BaseModel):
    """Manager updates nudge status."""
    status: str  # fulfilled or dismissed


# === Role Schemas ===

class RoleCreateRequest(BaseModel):
    """Request to create a new role with a leveling guide."""
    role_name: str
    company_url: str  # For context in example generation


class RoleResponse(BaseModel):
    id: str
    company_id: str
    name: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LevelResponse(BaseModel):
    id: str
    company_id: str
    role_id: str
    name: str
    order_idx: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetencyResponse(BaseModel):
    id: str
    company_id: str
    role_id: str
    name: str
    order_idx: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DefinitionResponse(BaseModel):
    id: str
    company_id: str
    role_id: str
    level_id: str
    competency_id: str
    definition: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExampleResponse(BaseModel):
    id: str
    company_id: str
    role_id: str
    level_id: str
    competency_id: str
    content: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Role Detail Response (for viewing a complete leveling guide) ===

class DefinitionWithExamplesResponse(BaseModel):
    """A definition with its examples for display."""
    id: str
    level_id: str
    level_name: str
    competency_id: str
    competency_name: str
    definition: str
    examples: List[ExampleResponse] = []

    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """Complete role with levels, competencies, definitions, and examples."""
    id: str
    company_id: str
    name: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    levels: List[LevelResponse] = []
    competencies: List[CompetencyResponse] = []
    definitions: List[DefinitionWithExamplesResponse] = []

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    """List of roles for a company."""
    roles: List[RoleResponse]


# === Processing Status ===

class ProcessingStatusResponse(BaseModel):
    """Status of an ongoing role processing."""
    role_id: str
    status: str  # processing, completed, failed
    message: Optional[str] = None


# === Internal Schemas (for OpenAI parsing) ===

class ParsedCell(BaseModel):
    """A cell parsed from the leveling guide."""
    level_name: str
    competency_name: str
    requirement: str


class ParsedLevelingGuide(BaseModel):
    """The structured output from parsing a leveling guide file."""
    levels: List[str]  # Ordered list of level names
    competencies: List[str]  # Ordered list of competency names
    cells: List[ParsedCell]  # All cells with their requirements


# === Prompt Management Schemas ===

class PromptResponse(BaseModel):
    """A prompt stored in the database."""
    id: str
    key: str
    name: str
    description: Optional[str] = None
    system_message: str
    user_message_template: str
    model: str
    temperature: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_message: Optional[str] = None
    user_message_template: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[str] = None


class PromptListResponse(BaseModel):
    """List of prompts."""
    prompts: List[PromptResponse]
