from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.business import HealthGoal
from app.schemas.business import (
    GoalStatusUpdate,
    HealthGoalCreate,
    HealthGoalRead,
    HealthGoalUpdate,
)

router = APIRouter(prefix="/goals", tags=["goals"])


def get_owned_goal(db: Session, user_id: str, goal_id: str) -> HealthGoal:
    goal = db.get(HealthGoal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.get("", response_model=list[HealthGoalRead])
def list_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[HealthGoal]:
    return list(
        db.scalars(
            select(HealthGoal)
            .where(HealthGoal.user_id == current_user.id)
            .order_by(HealthGoal.created_at.desc())
        )
    )


@router.post("", response_model=HealthGoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: HealthGoalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HealthGoal:
    goal = HealthGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=HealthGoalRead)
def update_goal(
    goal_id: str,
    payload: HealthGoalUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HealthGoal:
    goal = get_owned_goal(db, current_user.id, goal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{goal_id}/status", response_model=HealthGoalRead)
def update_goal_status(
    goal_id: str,
    payload: GoalStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HealthGoal:
    goal = get_owned_goal(db, current_user.id, goal_id)
    goal.status = payload.status
    db.commit()
    db.refresh(goal)
    return goal
