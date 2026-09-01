from sqlalchemy.orm import Session

from .model import Dish


class DishRepository:

    def create(
        self,
        db: Session,
        dish: Dish
    ):

        db.add(dish)
        db.commit()
        db.refresh(dish)

        return dish


    def list(self, db: Session):

        return (
            db.query(Dish)
            .filter(Dish.active == True)
            .order_by(Dish.name.asc())
            .all()
        )


    def get(
        self,
        db: Session,
        dish_id
    ):

        return (
            db.query(Dish)
            .filter(Dish.id == dish_id)
            .first()
        )


    def update(
        self,
        db: Session,
        dish: Dish
    ):

        db.commit()
        db.refresh(dish)

        return dish


    def delete(
        self,
        db: Session,
        dish: Dish
    ):

        dish.active = False

        db.commit()

        return dish