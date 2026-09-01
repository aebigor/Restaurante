from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from fastapi import Depends
from uuid import UUID
from app.core.database import get_db
from app.modules.dashboard.service import DashboardService


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# ======================================================
# LOGIN
# ======================================================

@router.get("/")
async def login(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={}
    )


# ======================================================
# DASHBOARD
# ======================================================

@router.get("/admin")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    dashboard = DashboardService(db)

    datos = dashboard.get_dashboard()

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context=datos
    )


# ======================================================
# MESAS
# ======================================================

@router.get("/admin/tables")
async def tables(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/tables/index.html",
        context={}
    )


@router.get("/admin/tables/create")
async def tables_create(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/tables/create.html",
        context={}
    )


# ======================================================
# CONFIGURACIÓN
# ======================================================

@router.get("/admin/settings")
async def settings(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/settings/index.html",
        context={}
    )


# ======================================================
# CATEGORÍAS
# ======================================================

@router.get("/admin/menu/categories")
async def categories(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/categories/index.html",
        context={}
    )
# ======================================================
# CREAR CATEGORÍA
# ======================================================

@router.get("/admin/menu/categories/create")
async def categories_create(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/categories/create.html",
        context={}
    )

# ======================================================
# EDITAR CATEGORÍA
# ======================================================

@router.get("/admin/menu/categories/edit/{category_id}")
async def categories_edit(
    request: Request,
    category_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/categories/edit.html",
        context={
            "category_id": category_id
        }
    )

# ======================================================
# PRODUCTOS
# ======================================================

@router.get("/admin/menu/products")
async def products(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/products/index.html",
        context={}
    )


@router.get("/admin/menu/products/create")
async def products_create(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/products/create.html",
        context={}
    )


@router.get("/admin/menu/products/edit/{product_id}")
async def products_edit(
    request: Request,
    product_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/products/edit.html",
        context={
            "product_id": product_id
        }
    )


# ======================================================
# COCINA / ESTACIONES
# ======================================================

@router.get("/admin/kitchen")
async def kitchen_dashboard(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/kitchen/index.html",
        context={}
    )


# ======================================================
# MENÚ DIGITAL
# ======================================================

@router.get("/admin/menu")
async def menu_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/index.html",
        context={}
    )


@router.get("/admin/menu/create")
async def menu_create(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/create.html",
        context={}
    )


@router.get("/admin/menu/edit/{menu_id}")
async def menu_edit(
    request: Request,
    menu_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/edit.html",
        context={
            "menu_id": menu_id
        }
    )

# ======================================================
# QR DEL MENÚ
# ======================================================

@router.get("/admin/menu/{menu_id}/qrs")
async def menu_qrs(
    request: Request,
    menu_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/menu/qrs.html",
        context={
            "menu_id": menu_id
        }
    )

# ======================================================
# PLATOS
# ======================================================

@router.get("/admin/dishes")
async def dishes(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/dishes/index.html",
        context={}
    )


@router.get("/admin/dishes/create")
async def dishes_create(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin/dishes/create.html",
        context={}
    )


@router.get("/admin/dishes/edit/{dish_id}")
async def dishes_edit(
    request: Request,
    dish_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/dishes/edit.html",
        context={
            "dish_id": dish_id
        }
    )


@router.get("/admin/dishes/view/{dish_id}")
async def dishes_view(
    request: Request,
    dish_id: UUID
):

    return templates.TemplateResponse(
        request=request,
        name="admin/dishes/view.html",
        context={
            "dish_id": dish_id
        }
    )

# ======================================================
# MENÚ PÚBLICO DEL CLIENTE
# ======================================================
@router.get("/m/{table_number}")
async def customer_menu(request: Request, table_number: int, db: Session = Depends(get_db)):
    from app.modules.dishes.model import Dish
    from app.modules.categories.model import Category
    from app.modules.tables.model import Table
    table = db.query(Table).filter(Table.number == table_number, Table.active == True).first()
    if not table:
        from fastapi import HTTPException
        raise HTTPException(404, "Mesa no encontrada")
    categories = db.query(Category).filter(Category.active == True).order_by(Category.display_order.asc(), Category.name.asc()).all()
    dishes = db.query(Dish).filter(Dish.active == True, Dish.available == True).order_by(Dish.name.asc()).all()
    return templates.TemplateResponse(request=request, name="public/menu.html", context={"table_number": table_number, "table_id": table.id, "categories": categories, "dishes": dishes})

@router.get("/waiter")
async def waiter_view(request: Request):
    return templates.TemplateResponse(request=request, name="waiter/index.html", context={})

@router.get("/kitchen")
async def kitchen_selector(request: Request):
    return templates.TemplateResponse(request=request, name="kitchen/index.html", context={})


@router.get("/kitchen/{screen_code}")
async def kitchen_view(request: Request, screen_code: str):
    return templates.TemplateResponse(request=request, name="kitchen/index.html", context={})
