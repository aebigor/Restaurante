from sqlalchemy.orm import Session
from fastapi import HTTPException
from .repository import OrderItemRepository
from .model import OrderItem
from app.modules.products.model import Product
from app.modules.dishes.model import Dish
from app.modules.order_batches.service import OrderBatchService
from app.modules.kitchen_queue.model import KitchenQueue

repository = OrderItemRepository()
batch_service = OrderBatchService()

class OrderItemService:
    def create(self, db: Session, data):
        if not data.dish_id and not data.product_id:
            raise HTTPException(400, "Debe seleccionar un plato")
        dish = db.query(Dish).filter(Dish.id == data.dish_id).first() if data.dish_id else None
        product = db.query(Product).filter(Product.id == data.product_id).first() if data.product_id else None
        if data.dish_id and not dish:
            raise HTTPException(404, "Plato no encontrado")
        if data.product_id and not product:
            raise HTTPException(404, "Producto no encontrado")
        source = dish or product
        station_id = source.station_id
        price = source.price
        batch = batch_service.get_or_create(db, data.order_id, station_id)
        item = OrderItem(order_id=data.order_id, product_id=data.product_id, dish_id=data.dish_id, quantity=data.quantity, unit_price=price, total=price * data.quantity, notes=data.notes)
        repository.create(db, item)
        queue = KitchenQueue(station_id=station_id, order_item_id=item.id)
        db.add(queue); db.commit(); db.refresh(item)
        return {"message": "Producto agregado", "batch": str(batch.id), "queue": str(queue.id), "item": str(item.id)}
    def list(self, db: Session):
        return repository.get_all(db)
