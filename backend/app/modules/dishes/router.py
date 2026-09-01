from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException, UploadFile, File

from sqlalchemy.orm import Session
from pathlib import Path
import uuid

from app.core.database import get_db

from .schemas import DishCreate
from .schemas import DishResponse
from .service import DishService


router = APIRouter(

    prefix="/api/dishes",

    tags=["Dishes"]

)

service = DishService()

@router.post("/upload-image")
async def upload_dish_image(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp", "image/avif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Formato de imagen no permitido")
    ext = Path(file.filename or "imagen.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    folder = Path("app/static/uploads/dishes")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename
    target.write_bytes(await file.read())
    return {"url": f"/static/uploads/dishes/{filename}"}


# ==========================================================
# LISTAR
# ==========================================================

@router.get(
    "/",
    response_model=list[DishResponse]
)
def list_dishes(

    db: Session = Depends(get_db)

):

    return service.list(db)


# ==========================================================
# OBTENER
# ==========================================================

@router.get(
    "/{dish_id}",
    response_model=DishResponse
)
def get_dish(

    dish_id: str,

    db: Session = Depends(get_db)

):

    dish = service.get(

        db,

        dish_id

    )

    if not dish:

        raise HTTPException(

            status_code=404,

            detail="Plato no encontrado."

        )

    return dish


# ==========================================================
# CREAR
# ==========================================================

@router.post(
    "/",
    response_model=DishResponse
)
def create_dish(

    data: DishCreate,

    db: Session = Depends(get_db)

):

    return service.create(

        db,

        data

    )


# ==========================================================
# ACTUALIZAR
# ==========================================================

@router.put(
    "/{dish_id}",
    response_model=DishResponse
)
def update_dish(

    dish_id: str,

    data: DishCreate,

    db: Session = Depends(get_db)

):

    dish = service.update(

        db,

        dish_id,

        data

    )

    if not dish:

        raise HTTPException(

            status_code=404,

            detail="Plato no encontrado."

        )

    return dish


# ==========================================================
# ELIMINAR
# ==========================================================

@router.delete(
    "/{dish_id}"
)
def delete_dish(

    dish_id: str,

    db: Session = Depends(get_db)

):

    dish = service.delete(

        db,

        dish_id

    )

    if not dish:

        raise HTTPException(

            status_code=404,

            detail="Plato no encontrado."

        )

    return {

        "message": "Plato eliminado correctamente."

    }