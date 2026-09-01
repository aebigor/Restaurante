"""
=========================================================
Router Principal

Aquí se registran todos los módulos del sistema.

main.py solamente importa este archivo.

Cuando agreguemos nuevos módulos simplemente
se registrarán aquí.
=========================================================
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.tables.router import router as table_router
from app.modules.sessions.router import router as sessions_router
from app.modules.stations.router import router as stations_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router
from app.modules.order_items.router import router as order_items_router
from app.modules.kitchen_tickets.router import router as kitchen_ticket_router
from app.modules.kitchen_queue.router import router as kitchen_queue_router
from app.modules.order_batches.router import router as order_batch_router
from app.modules.categories.router import router as category_router
from app.modules.menu.router import router as menu_router
from app.modules.dishes.router import router as dishes_router
from app.modules.waiter_calls.router import router as waiter_calls_router
from app.modules.screens.router import router as screens_router
from app.modules.waiter.router import router as waiter_router
from app.modules.waiter_calls.router import router as waiter_calls_router
from app.modules.menu_items.router import router as menu_items_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(table_router)
api_router.include_router(sessions_router)
api_router.include_router(stations_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(order_items_router)
api_router.include_router(kitchen_ticket_router)
api_router.include_router(kitchen_queue_router)
api_router.include_router(order_batch_router)
api_router.include_router(category_router)
api_router.include_router(menu_router)
api_router.include_router(dishes_router)
api_router.include_router(menu_items_router)
api_router.include_router(waiter_calls_router)
api_router.include_router(waiter_router)
api_router.include_router(screens_router)
