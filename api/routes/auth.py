from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database
from models import User
from schemas.auth import LoginRequest, LoginResponse
from api.auth_handler import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(database.get_db)):
    role = payload.role.strip().lower()

    if role not in ["manufacturer", "driver", "retailer"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    email = payload.email.strip().lower()
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.role.strip().lower() != role:
            raise HTTPException(
                status_code=403,
                detail="This email is already registered under a different role."
            )
        user.name = name
    else:
        user = User(name=name, email=email, role=role)
        db.add(user)

    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email, "role": user.role})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

# anything
