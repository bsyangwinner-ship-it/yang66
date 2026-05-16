from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.business import HealthProfile, UserFitnessProfile
from app.schemas.business import (
    FitnessProfileRead,
    FitnessProfileUpsert,
    HealthProfileRead,
    HealthProfileUpsert,
)

router = APIRouter(tags=["profile"])


@router.get("/profile/me", response_model=HealthProfileRead)
def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HealthProfile:
    profile = db.scalar(select(HealthProfile).where(HealthProfile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/profile/me", response_model=HealthProfileRead)
def upsert_profile(
    payload: HealthProfileUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HealthProfile:
    profile = db.scalar(select(HealthProfile).where(HealthProfile.user_id == current_user.id))
    if profile is None:
        profile = HealthProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/fitness-profile/me", response_model=FitnessProfileRead)
def get_fitness_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserFitnessProfile:
    profile = db.scalar(
        select(UserFitnessProfile).where(UserFitnessProfile.user_id == current_user.id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness profile not found",
        )
    return profile


@router.put("/fitness-profile/me", response_model=FitnessProfileRead)
def upsert_fitness_profile(
    payload: FitnessProfileUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserFitnessProfile:
    profile = db.scalar(
        select(UserFitnessProfile).where(UserFitnessProfile.user_id == current_user.id)
    )
    if profile is None:
        profile = UserFitnessProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
