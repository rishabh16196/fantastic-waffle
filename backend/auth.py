"""
Simple auth helpers for the prototype.

This is a simplified auth system that:
- Uses email + company association (no passwords)
- Stores user ID in a simple header (X-User-ID)
- For prototype purposes only - not production ready

In production, you would use:
- JWT tokens or session cookies
- Password hashing
- Email verification
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from typing import Optional

from database import get_db
from models import User, Company


def get_current_user(
    x_user_id: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user from the X-User-ID header.
    Returns None if no user ID provided.
    """
    if not x_user_id:
        return None
    
    user = db.query(User).filter(User.id == x_user_id).first()
    return user


def require_user(
    x_user_id: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> User:
    """
    Require a valid user. Raises 401 if not authenticated.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    return user


def require_manager(
    user: User = Depends(require_user)
) -> User:
    """
    Require a manager role. Raises 403 if not a manager.
    """
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    return user


def require_employee(
    user: User = Depends(require_user)
) -> User:
    """
    Require an employee role. Raises 403 if not an employee.
    """
    if user.role != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    return user
