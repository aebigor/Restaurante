from uuid import UUID
from io import BytesIO

import qrcode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.modules.tables.model import Table

from .schemas import (
    MenuCreate,
    MenuUpdate,
    MenuResponse
)

from .service import MenuService


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/api/menu",
    tags=["Menu"]
)


service = MenuService()


# ==========================================================
# LISTAR MENÚS
# ==========================================================

@router.get(
    "/",
    response_model=list[MenuResponse]
)
def list_menu(
    db: Session = Depends(get_db)
):

    return service.list(db)


# ==========================================================
# MENÚ ACTIVO
# ==========================================================

@router.get(
    "/active",
    response_model=MenuResponse
)
def get_active_menu(
    db: Session = Depends(get_db)
):

    menu = service.get_active(db)

    if not menu:

        raise HTTPException(
            status_code=404,
            detail="No existe un menú activo."
        )

    return menu


# ==========================================================
# OBTENER MENÚ
# ==========================================================

@router.get(
    "/{menu_id}",
    response_model=MenuResponse
)
def get_menu(
    menu_id: UUID,
    db: Session = Depends(get_db)
):

    menu = service.get(
        db,
        menu_id
    )


    if not menu:

        raise HTTPException(
            status_code=404,
            detail="Menú no encontrado."
        )


    return menu


# ==========================================================
# CREAR MENÚ
# ==========================================================

@router.post(
    "/",
    response_model=MenuResponse
)
def create_menu(
    data: MenuCreate,
    db: Session = Depends(get_db)
):

    try:

        return service.create(
            db,
            data
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==========================================================
# ACTUALIZAR MENÚ
# ==========================================================

@router.put(
    "/{menu_id}",
    response_model=MenuResponse
)
def update_menu(
    menu_id: UUID,
    data: MenuUpdate,
    db: Session = Depends(get_db)
):

    try:

        return service.update(
            db,
            menu_id,
            data
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==========================================================
# ELIMINAR MENÚ
# ==========================================================

@router.delete(
    "/{menu_id}"
)
def delete_menu(
    menu_id: UUID,
    db: Session = Depends(get_db)
):

    try:

        service.delete(
            db,
            menu_id
        )

        return {
            "message": "Menú eliminado correctamente."
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==========================================================
# QR DE TODAS LAS MESAS
# ==========================================================

@router.get(
    "/{menu_id}/qrs"
)
def get_menu_qrs(
    menu_id: UUID,
    db: Session = Depends(get_db)
):

    menu = service.get(
        db,
        menu_id
    )


    if not menu:

        raise HTTPException(
            status_code=404,
            detail="Menú no encontrado."
        )


    # ======================================================
    # SOLO PERMITIMOS VER QR DEL MENÚ ACTIVO
    # ======================================================

    if not menu.active:

        raise HTTPException(
            status_code=400,
            detail=(
                "Los QRs se generan para el menú activo. "
                "Activa este menú primero."
            )
        )


    tables = (
        db.query(Table)
        .filter(
            Table.active == True
        )
        .order_by(
            Table.number.asc()
        )
        .all()
    )


    result = []


    for table in tables:

        # ==================================================
        # URL QUE QUEDARÁ DENTRO DEL QR
        # ==================================================

        url = f"/m/{table.number}"


        result.append({

            "table_id": table.id,

            "table_number": table.number,

            "table_name": table.name,

            "zone": table.zone,

            "capacity": table.capacity,

            "url": url,

            "qr_url": (
                f"/api/menu/{menu.id}/qrs/"
                f"{table.id}/image"
            )

        })


    return {

        "menu": {

            "id": str(menu.id),

            "title": menu.title,

            "slug": menu.slug,

            "active": menu.active

        },

        "total_tables": len(result),

        "tables": result

    }


# ==========================================================
# GENERAR IMAGEN QR
# ==========================================================

@router.get(
    "/{menu_id}/qrs/{table_id}/image"
)
def generate_table_qr(
    menu_id: UUID,
    table_id: int,
    db: Session = Depends(get_db)
):

    menu = service.get(
        db,
        menu_id
    )


    if not menu:

        raise HTTPException(
            status_code=404,
            detail="Menú no encontrado."
        )


    if not menu.active:

        raise HTTPException(
            status_code=400,
            detail="Este menú no está activo."
        )


    table = (
        db.query(Table)
        .filter(
            Table.id == table_id,
            Table.active == True
        )
        .first()
    )


    if not table:

        raise HTTPException(
            status_code=404,
            detail="Mesa no encontrada o inactiva."
        )


    # ======================================================
    # CREAR URL ABSOLUTA
    # ======================================================

    # La URL base se envía desde el navegador mediante
    # el endpoint de datos. Para el QR usamos una URL
    # relativa que el navegador convertirá en absoluta
    # en la página de impresión.
    #
    # Sin embargo, para que el QR funcione desde otro
    # dispositivo necesitamos la URL real del servidor.
    #
    # Se obtiene desde la petición.
    # ======================================================

    from fastapi import Request


    # Esta función necesita Request.
    # El endpoint se vuelve a manejar abajo.
    #
    # Este bloque no se utiliza directamente.
    # ======================================================

    url = f"/m/{table.number}"


    # ======================================================
    # GENERAR QR
    # ======================================================

    qr = qrcode.QRCode(

        version=None,

        error_correction=qrcode.constants.ERROR_CORRECT_M,

        box_size=10,

        border=4

    )


    qr.add_data(url)

    qr.make(
        fit=True
    )


    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )


    output = BytesIO()

    image.save(
        output,
        format="PNG"
    )


    output.seek(0)


    return StreamingResponse(

        output,

        media_type="image/png",

        headers={
            "Content-Disposition": (
                f'inline; filename="mesa-'
                f'{table.number}-qr.png"'
            )
        }

    )