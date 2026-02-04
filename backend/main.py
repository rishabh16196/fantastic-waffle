"""
FastAPI application for the Leveling Guide Example Generator.

Endpoints:
- Auth: Register manager, join as employee, login, get current user
- Roles: Create, list, get leveling guides (company-scoped)
- Nudges: Create, list, update guide requests
"""

import os
from typing import List, Optional
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession
from dotenv import load_dotenv

from database import get_db, init_db
from models import Company, User, Nudge, Role, Level, Competency, Definition, Example, DefinitionQualityMetrics
from schemas import (
    RoleResponse, RoleDetailResponse, RoleListResponse, LevelResponse, CompetencyResponse,
    DefinitionWithExamplesResponse, ExampleResponse, DefinitionQualityMetricsResponse, ProcessingStatusResponse,
    ManagerRegisterRequest, EmployeeJoinRequest, LoginRequest, AuthResponse, MeResponse, UserResponse, CompanyResponse,
    NudgeCreateRequest, NudgeResponse, NudgeUpdateRequest,
    PromptResponse, PromptUpdateRequest, PromptListResponse
)
from file_parser import extract_text
from openai_service import process_and_save_leveling_guide
from auth import get_current_user, require_user, require_manager
from prompt_service import seed_default_prompts, list_prompts, get_prompt, update_prompt, set_prompt_active
from validations import sanitize_error

load_dotenv()

app = FastAPI(
    title="Leveling Guide Example Generator",
    description="Generate specific examples for career leveling guides using AI",
    version="3.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Processing status tracking (in-memory for simplicity)
_processing_status = {}


@app.on_event("startup")
def startup():
    """Initialize database and seed default prompts on startup."""
    from database import SessionLocal
    
    init_db()
    
    # Seed default prompts if they don't exist
    db = SessionLocal()
    try:
        created = seed_default_prompts(db)
        if created > 0:
            print(f"Seeded {created} default prompt(s)")
    finally:
        db.close()


# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register-manager", response_model=AuthResponse)
def register_manager(request: ManagerRegisterRequest, db: DBSession = Depends(get_db)):
    """
    Manager creates a new company and their account.
    Returns user info and company with invite code.
    """
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    company = Company(
        name=request.company_name,
        domain=request.company_domain
    )
    db.add(company)
    db.flush()
    
    user = User(
        email=request.email,
        name=request.name,
        role="manager",
        company_id=company.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(company)
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        company=CompanyResponse(
            id=company.id,
            name=company.name,
            domain=company.domain,
            invite_code=company.invite_code,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    )


@app.post("/api/auth/join-company", response_model=AuthResponse)
def join_company(request: EmployeeJoinRequest, db: DBSession = Depends(get_db)):
    """Employee joins an existing company via invite code."""
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    company = db.query(Company).filter(Company.invite_code == request.invite_code).first()
    if not company:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    user = User(
        email=request.email,
        name=request.name,
        role="employee",
        company_id=company.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        company=CompanyResponse(
            id=company.id,
            name=company.name,
            domain=company.domain,
            invite_code=company.invite_code,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: DBSession = Depends(get_db)):
    """Login with email (simple auth - no password)."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email")
    
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        company=CompanyResponse(
            id=company.id,
            name=company.name,
            domain=company.domain,
            invite_code=company.invite_code if user.role == "manager" else "",
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    )


@app.get("/api/auth/me", response_model=MeResponse)
def get_me(user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    """Get current user info with company details."""
    company = db.query(Company).filter(Company.id == user.company_id).first()
    
    return MeResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        company=CompanyResponse(
            id=company.id,
            name=company.name,
            domain=company.domain,
            invite_code=company.invite_code if user.role == "manager" else "",
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    )


# ==================== COMPANY ENDPOINTS ====================

@app.get("/api/company/users", response_model=List[UserResponse])
def get_company_users(user: User = Depends(require_manager), db: DBSession = Depends(get_db)):
    """Manager gets list of all users in their company."""
    users = db.query(User).filter(
        User.company_id == user.company_id,
        User.is_active == True
    ).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            company_id=u.company_id,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at
        )
        for u in users
    ]


# ==================== NUDGE ENDPOINTS ====================

@app.post("/api/nudges", response_model=NudgeResponse)
def create_nudge(
    request: NudgeCreateRequest,
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """Employee creates a request for a missing leveling guide."""
    existing = db.query(Nudge).filter(
        Nudge.company_id == user.company_id,
        Nudge.role_name == request.role_name,
        Nudge.status == "pending",
        Nudge.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="A request for this role already exists")
    
    nudge = Nudge(
        employee_id=user.id,
        company_id=user.company_id,
        role_name=request.role_name,
        level_name=request.level_name,
        status="pending"
    )
    db.add(nudge)
    db.commit()
    db.refresh(nudge)
    
    return NudgeResponse(
        id=nudge.id,
        employee_id=nudge.employee_id,
        company_id=nudge.company_id,
        role_name=nudge.role_name,
        level_name=nudge.level_name,
        status=nudge.status,
        is_active=nudge.is_active,
        created_at=nudge.created_at,
        updated_at=nudge.updated_at,
        employee_name=user.name
    )


@app.get("/api/nudges", response_model=List[NudgeResponse])
def list_nudges(user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    """List nudges for the user's company."""
    query = db.query(Nudge).filter(
        Nudge.company_id == user.company_id,
        Nudge.is_active == True
    )
    
    if user.role == "employee":
        query = query.filter(Nudge.employee_id == user.id)
    
    nudges = query.order_by(Nudge.created_at.desc()).all()
    
    result = []
    for nudge in nudges:
        employee = db.query(User).filter(User.id == nudge.employee_id).first()
        result.append(NudgeResponse(
            id=nudge.id,
            employee_id=nudge.employee_id,
            company_id=nudge.company_id,
            role_name=nudge.role_name,
            level_name=nudge.level_name,
            status=nudge.status,
            is_active=nudge.is_active,
            created_at=nudge.created_at,
            updated_at=nudge.updated_at,
            employee_name=employee.name if employee else None
        ))
    
    return result


@app.patch("/api/nudges/{nudge_id}", response_model=NudgeResponse)
def update_nudge(
    nudge_id: str,
    request: NudgeUpdateRequest,
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """Manager updates nudge status (fulfilled or dismissed)."""
    nudge = db.query(Nudge).filter(
        Nudge.id == nudge_id,
        Nudge.company_id == user.company_id
    ).first()
    
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")
    
    if request.status not in ["fulfilled", "dismissed"]:
        raise HTTPException(status_code=400, detail="Status must be 'fulfilled' or 'dismissed'")
    
    nudge.status = request.status
    db.commit()
    db.refresh(nudge)
    
    employee = db.query(User).filter(User.id == nudge.employee_id).first()
    
    return NudgeResponse(
        id=nudge.id,
        employee_id=nudge.employee_id,
        company_id=nudge.company_id,
        role_name=nudge.role_name,
        level_name=nudge.level_name,
        status=nudge.status,
        is_active=nudge.is_active,
        created_at=nudge.created_at,
        updated_at=nudge.updated_at,
        employee_name=employee.name if employee else None
    )


# ==================== ROLE ENDPOINTS ====================

def process_role_in_background(
    role_id: str,
    company_id: str,
    role_name: str,
    company_url: str,
    file_content: str
):
    """Background task to process a role's leveling guide."""
    from database import SessionLocal
    
    global _processing_status
    _processing_status[role_id] = {"status": "processing", "message": "Parsing leveling guide..."}
    
    db = SessionLocal()
    try:
        # Delete the placeholder role we created
        placeholder = db.query(Role).filter(Role.id == role_id).first()
        if placeholder:
            db.delete(placeholder)
            db.flush()
        
        # Process and save the leveling guide
        role = process_and_save_leveling_guide(
            db=db,
            company_id=company_id,
            role_name=role_name,
            company_url=company_url,
            raw_text=file_content
        )
        
        _processing_status[role_id] = {
            "status": "completed",
            "message": "Processing complete",
            "new_role_id": role.id
        }
        
    except Exception as e:
        _processing_status[role_id] = {
            "status": "failed",
            "message": sanitize_error(e)
        }
    finally:
        db.close()


@app.get("/api/roles/check")
def check_role_exists(
    role_name: str,
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """Check if a role with this name already exists for the company."""
    existing_role = db.query(Role).filter(
        Role.company_id == user.company_id,
        Role.name == role_name,
        Role.is_active == True
    ).first()
    
    return {
        "exists": existing_role is not None,
        "role_id": existing_role.id if existing_role else None,
        "created_at": existing_role.created_at.isoformat() if existing_role else None
    }


@app.post("/api/roles", response_model=RoleResponse)
async def create_role(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_url: str = Form(...),
    role_name: str = Form(...),
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """
    Create a new role by uploading a leveling guide file.
    Manager only - creates guide for their company.
    
    The file will be parsed and examples will be generated in the background.
    Poll GET /api/roles/{id}/status to check when processing is complete.
    """
    # Read and extract text from file
    file_content = await file.read()
    text_content = extract_text(file_content, file.filename or "file.txt")
    
    # Create a placeholder role for status tracking
    role = Role(
        company_id=user.company_id,
        name=role_name
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Process in background
    background_tasks.add_task(
        process_role_in_background,
        role.id,
        user.company_id,
        role_name,
        company_url,
        text_content
    )
    
    return RoleResponse(
        id=role.id,
        company_id=role.company_id,
        name=role.name,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at
    )


@app.get("/api/roles/{role_id}/status", response_model=ProcessingStatusResponse)
def get_role_status(
    role_id: str,
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """Check the processing status of a role."""
    global _processing_status
    
    if role_id in _processing_status:
        status_info = _processing_status[role_id]
        return ProcessingStatusResponse(
            role_id=status_info.get("new_role_id", role_id),
            status=status_info["status"],
            message=status_info.get("message")
        )
    
    # Check if role exists and is complete
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.company_id == user.company_id,
        Role.is_active == True
    ).first()
    
    if role:
        return ProcessingStatusResponse(
            role_id=role.id,
            status="completed",
            message="Role is ready"
        )
    
    raise HTTPException(status_code=404, detail="Role not found")


@app.get("/api/roles/{role_id}", response_model=RoleDetailResponse)
def get_role(
    role_id: str,
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """Get full role details including levels, competencies, definitions, and examples."""
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.is_active == True
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check company access
    if role.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get levels sorted by order
    levels = db.query(Level).filter(
        Level.role_id == role_id,
        Level.is_active == True
    ).order_by(Level.order_idx).all()
    
    # Get competencies sorted by order
    competencies = db.query(Competency).filter(
        Competency.role_id == role_id,
        Competency.is_active == True
    ).order_by(Competency.order_idx).all()
    
    # Create maps for names
    level_names = {l.id: l.name for l in levels}
    competency_names = {c.id: c.name for c in competencies}
    
    # Get definitions
    definitions = db.query(Definition).filter(
        Definition.role_id == role_id,
        Definition.is_active == True
    ).all()
    
    # Get ALL examples for this role in ONE query (fixes N+1 problem)
    all_examples = db.query(Example).filter(
        Example.role_id == role_id,
        Example.is_active == True
    ).all()
    
    # Group examples by (level_id, competency_id) for fast lookup
    examples_map = defaultdict(list)
    for ex in all_examples:
        key = (ex.level_id, ex.competency_id)
        examples_map[key].append(ex)
    
    definitions_response = []
    for defn in definitions:
        # Look up examples from the pre-fetched map (O(1) instead of DB query)
        examples = examples_map.get((defn.level_id, defn.competency_id), [])
        
        definitions_response.append(DefinitionWithExamplesResponse(
            id=defn.id,
            level_id=defn.level_id,
            level_name=level_names.get(defn.level_id, ""),
            competency_id=defn.competency_id,
            competency_name=competency_names.get(defn.competency_id, ""),
            definition=defn.definition,
            examples=[
                ExampleResponse(
                    id=ex.id,
                    company_id=ex.company_id,
                    role_id=ex.role_id,
                    level_id=ex.level_id,
                    competency_id=ex.competency_id,
                    content=ex.content,
                    is_active=ex.is_active,
                    created_at=ex.created_at,
                    updated_at=ex.updated_at
                )
                for ex in examples
            ]
        ))
    
    return RoleDetailResponse(
        id=role.id,
        company_id=role.company_id,
        name=role.name,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        levels=[
            LevelResponse(
                id=l.id,
                company_id=l.company_id,
                role_id=l.role_id,
                name=l.name,
                order_idx=l.order_idx,
                is_active=l.is_active,
                created_at=l.created_at,
                updated_at=l.updated_at
            )
            for l in levels
        ],
        competencies=[
            CompetencyResponse(
                id=c.id,
                company_id=c.company_id,
                role_id=c.role_id,
                name=c.name,
                order_idx=c.order_idx,
                is_active=c.is_active,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in competencies
        ],
        definitions=definitions_response
    )


@app.get("/api/roles/{role_id}/quality-metrics", response_model=List[DefinitionQualityMetricsResponse])
def get_role_quality_metrics(
    role_id: str,
    prompt_id: Optional[str] = None,
    prompt_version: Optional[int] = None,
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """Get per-cell quality proxy metrics for a role."""
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.is_active == True
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    metrics_query = db.query(DefinitionQualityMetrics).filter(
        DefinitionQualityMetrics.role_id == role_id,
        DefinitionQualityMetrics.company_id == user.company_id,
        DefinitionQualityMetrics.is_active == True
    )

    if prompt_id:
        metrics_query = metrics_query.filter(DefinitionQualityMetrics.prompt_id == prompt_id)
    if prompt_version is not None:
        metrics_query = metrics_query.filter(DefinitionQualityMetrics.prompt_version == prompt_version)

    metrics = metrics_query.all()

    return metrics


@app.get("/api/roles", response_model=List[RoleResponse])
def list_roles(
    user: User = Depends(require_user),
    db: DBSession = Depends(get_db)
):
    """List all roles for the user's company."""
    roles = db.query(Role).filter(
        Role.company_id == user.company_id,
        Role.is_active == True
    ).order_by(Role.created_at.desc()).all()
    
    return [
        RoleResponse(
            id=r.id,
            company_id=r.company_id,
            name=r.name,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in roles
    ]


# ==================== PROMPT MANAGEMENT ENDPOINTS ====================

@app.get("/api/prompts", response_model=List[PromptResponse])
def get_prompts(
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """
    List all prompts. Manager only.
    Use these to customize the AI behavior for parsing and example generation.
    """
    prompts = list_prompts(db)
    return [
        PromptResponse(
            id=p.id,
            key=p.key,
            name=p.name,
            description=p.description,
            system_message=p.system_message,
            user_message_template=p.user_message_template,
            model=p.model,
            temperature=p.temperature,
            version=p.version,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in prompts
    ]


@app.get("/api/prompts/{prompt_key}", response_model=PromptResponse)
def get_prompt_by_key(
    prompt_key: str,
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """Get a single prompt by its key. Manager only."""
    prompt = get_prompt(db, prompt_key)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return PromptResponse(
        id=prompt.id,
        key=prompt.key,
        name=prompt.name,
        description=prompt.description,
        system_message=prompt.system_message,
        user_message_template=prompt.user_message_template,
        model=prompt.model,
        temperature=prompt.temperature,
        version=prompt.version,
        is_active=prompt.is_active,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at
    )


@app.put("/api/prompts/{prompt_key}", response_model=PromptResponse)
def update_prompt_by_key(
    prompt_key: str,
    request: PromptUpdateRequest,
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """
    Update a prompt. Manager only.
    
    Available template variables:
    - parse_guide: {{raw_text}}
    - generate_examples: {{company_url}}, {{role_name}}, {{level_name}}, {{competency_name}}, {{requirement}}
    """
    prompt = update_prompt(
        db=db,
        key=prompt_key,
        name=request.name,
        description=request.description,
        system_message=request.system_message,
        user_message_template=request.user_message_template,
        model=request.model,
        temperature=request.temperature,
        is_active=request.is_active
    )
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return PromptResponse(
        id=prompt.id,
        key=prompt.key,
        name=prompt.name,
        description=prompt.description,
        system_message=prompt.system_message,
        user_message_template=prompt.user_message_template,
        model=prompt.model,
        temperature=prompt.temperature,
        version=prompt.version,
        is_active=prompt.is_active,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at
    )


@app.post("/api/prompts/{prompt_id}/activate", response_model=PromptResponse)
def activate_prompt_version(
    prompt_id: str,
    user: User = Depends(require_manager),
    db: DBSession = Depends(get_db)
):
    """Set a specific prompt version as active for its key."""
    prompt = set_prompt_active(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptResponse(
        id=prompt.id,
        key=prompt.key,
        name=prompt.name,
        description=prompt.description,
        system_message=prompt.system_message,
        user_message_template=prompt.user_message_template,
        model=prompt.model,
        temperature=prompt.temperature,
        version=prompt.version,
        is_active=prompt.is_active,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
