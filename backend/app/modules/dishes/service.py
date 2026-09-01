import uuid

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.categories.model import Category

from .model import Dish
from .repository import DishRepository
from .schemas import DishCreate


class DishService:

    def __init__(self):

        self.repository = DishRepository()


    # ======================================================
    # CREAR
    # ======================================================

    def create(
        self,
        db: Session,
        data: DishCreate
    ):

        category = db.query(Category).filter(
            Category.id == data.category_id,
            Category.active == True
        ).first()

        if not category:

            raise HTTPException(
                400,
                "La categoría no existe o está inactiva."
            )


        if not category.station_id:

            raise HTTPException(
                400,
                "La categoría debe tener una estación de cocina asignada antes de crear el plato."
            )


        if data.station_id != category.station_id:

            raise HTTPException(
                400,
                "La estación del plato debe coincidir con la estación de su categoría."
            )


        dish = Dish(

            id=uuid.uuid4(),

            name=data.name,

            price=data.price,

            category_id=data.category_id,

            station_id=data.station_id,

            preparation_time=data.preparation_time,

            portion=data.portion,

            image=data.image,

            featured=data.featured,

            available=data.available,

            active=True

        )


        return self.repository.create(
            db,
            dish
        )


    # ======================================================
    # LISTAR
    # ======================================================

    def list(
        self,
        db: Session
    ):

        dishes = self.repository.list(db)

        result = []


        for dish in dishes:

            result.append({

                "id": dish.id,

                "name": dish.name,

                "price": dish.price,

                "category_id": dish.category_id,

                "station_id": dish.station_id,

                "preparation_time": dish.preparation_time,

                "portion": dish.portion,

                "image": dish.image,

                "featured": dish.featured,

                "available": dish.available,

                "active": dish.active,

                "category_name": (
                    dish.category.name
                    if dish.category
                    else None
                ),

                "station_name": (
                    dish.station.name
                    if dish.station
                    else None
                )

            })


        return result


    # ======================================================
    # OBTENER
    # ======================================================

    def get(
        self,
        db: Session,
        dish_id
    ):

        return self.repository.get(
            db,
            dish_id
        )


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def update(
        self,
        db: Session,
        dish_id,
        data: DishCreate
    ):

        dish = self.repository.get(
            db,
            dish_id
        )


        if not dish:

            return None


        category = db.query(Category).filter(
            Category.id == data.category_id,
            Category.active == True
        ).first()


        if not category:

            raise HTTPException(
                400,
                "La categoría no existe o está inactiva."
            )


        if not category.station_id:

            raise HTTPException(
                400,
                "La categoría debe tener una estación de cocina asignada."
            )


        if data.station_id != category.station_id:

            raise HTTPException(
                400,
                "La estación del plato debe coincidir con la categoría."
            )


        dish.name = data.name

        dish.price = data.price

        dish.category_id = data.category_id

        dish.station_id = data.station_id

        dish.preparation_time = data.preparation_time

        dish.portion = data.portion

        dish.image = data.image

        dish.featured = data.featured

        dish.available = data.available


        return self.repository.update(
            db,
            dish
        )


    # ======================================================
    # ELIMINAR
    # ======================================================

    def delete(
        self,
        db: Session,
        dish_id
    ):

        dish = self.repository.get(
            db,
            dish_id
        )


        if not dish:

            return None


        return self.repository.delete(
            db,
            dish
        )