"""
Registrar todos los modelos del ERP.
"""

from app.modules.users.model import User
from app.modules.roles.model import Role

from app.modules.categories.model import Category
from app.modules.stations.model import Station
from app.modules.products.model import Product

from app.modules.tables.model import Table
from app.modules.sessions.model import Session

from app.modules.orders.model import Order
from app.modules.order_items.model import OrderItem

from app.modules.kitchen_tickets.model import KitchenTicket
from app.modules.kitchen_queue.model import KitchenQueue
from app.modules.order_batches.model import OrderBatch
from app.modules.dishes.model import Dish
from app.modules.waiter_calls.model import WaiterCall
from app.modules.screens.model import Screen

from app.modules.menu.model import Menu
from app.modules.menu_items.model import MenuItem