from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.business import FoodItem, Meal
from app.schemas.business import FoodItemCreate, MealCreate, MealRead, MealUpdate

router = APIRouter(prefix="/meals", tags=["meals"])


def get_owned_meal(db: Session, user_id: str, meal_id: str) -> Meal:
    meal = db.scalar(
        select(Meal).options(selectinload(Meal.food_items)).where(Meal.id == meal_id)
    )
    if meal is None or meal.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal


def build_food_item(payload: FoodItemCreate) -> FoodItem:
    return FoodItem(**payload.model_dump())


@router.get("", response_model=list[MealRead])
def list_meals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Meal]:
    query = (
        select(Meal)
        .options(selectinload(Meal.food_items))
        .where(Meal.user_id == current_user.id)
        .order_by(Meal.meal_date.desc(), Meal.created_at.desc())
    )
    if start_date is not None:
        query = query.where(Meal.meal_date >= start_date)
    if end_date is not None:
        query = query.where(Meal.meal_date <= end_date)
    return list(db.scalars(query))


@router.post("", response_model=MealRead, status_code=status.HTTP_201_CREATED)
def create_meal(
    payload: MealCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Meal:
    data = payload.model_dump(exclude={"food_items"})
    meal = Meal(user_id=current_user.id, **data)
    meal.food_items = [build_food_item(item) for item in payload.food_items]
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return get_owned_meal(db, current_user.id, meal.id)


@router.get("/{meal_id}", response_model=MealRead)
def get_meal(
    meal_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Meal:
    return get_owned_meal(db, current_user.id, meal_id)


@router.put("/{meal_id}", response_model=MealRead)
def update_meal(
    meal_id: str,
    payload: MealUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Meal:
    meal = get_owned_meal(db, current_user.id, meal_id)
    data = payload.model_dump(exclude_unset=True, exclude={"food_items"})
    for field, value in data.items():
        setattr(meal, field, value)

    if payload.food_items is not None:
        meal.food_items = [build_food_item(item) for item in payload.food_items]

    db.commit()
    db.refresh(meal)
    return get_owned_meal(db, current_user.id, meal.id)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    meal = get_owned_meal(db, current_user.id, meal_id)
    db.delete(meal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
