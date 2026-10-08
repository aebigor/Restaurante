from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.modules.inventory.model import InventoryItem, InventoryMovement
from .inventory_recipe_model import ProductInventoryRecipe


def get_recipe(db: Session, product_id):
    return (
        db.query(ProductInventoryRecipe)
        .options(joinedload(ProductInventoryRecipe.inventory_item))
        .filter(ProductInventoryRecipe.product_id == product_id)
        .all()
    )


def save_recipe(db: Session, product_id, recipe):
    db.query(ProductInventoryRecipe).filter(ProductInventoryRecipe.product_id == product_id).delete(synchronize_session=False)
    seen = set()
    for row in recipe or []:
        iid = row.inventory_item_id
        if iid in seen:
            raise HTTPException(400, "No puedes asociar dos veces el mismo insumo al producto.")
        seen.add(iid)
        item = db.query(InventoryItem).filter(InventoryItem.id == iid, InventoryItem.active.is_(True)).first()
        if not item:
            raise HTTPException(404, "Uno de los insumos de inventario no existe o está archivado.")
        qty = Decimal(str(row.quantity_per_sale))
        if qty <= 0:
            raise HTTPException(400, f"La cantidad por venta de '{item.name}' debe ser mayor que cero.")
        db.add(ProductInventoryRecipe(product_id=product_id, inventory_item_id=iid, quantity_per_sale=qty))


def consume_product_recipe(db: Session, product, sale_quantity, *, order_id=None):
    """Consume todos los insumos asociados al producto. Valida todo antes de modificar stock."""
    recipe = get_recipe(db, product.id)
    if not recipe:
        return False
    sale_qty = Decimal(str(sale_quantity))
    required = []
    for row in recipe:
        item = row.inventory_item
        qty = Decimal(str(row.quantity_per_sale)) * sale_qty
        current = Decimal(str(item.quantity or 0))
        if current < qty:
            raise HTTPException(409, f"Inventario insuficiente para '{item.name}'. Disponible: {current:g} {item.unit}; necesario: {qty:g}.")
        required.append((item, qty))
    short_order = str(order_id)[:8].upper() if order_id else "SIN-COMANDA"
    for item, qty in required:
        item.quantity = Decimal(str(item.quantity or 0)) - qty
        db.add(InventoryMovement(item_id=item.id, movement_type="SALIDA", quantity=qty, reason=f"Venta automática · Comanda {short_order} · Producto {product.name}"))
    return True
