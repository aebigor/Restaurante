"""
Lógica de consumo automático del inventario.

Los artículos de venta directa (bebidas, chorizos/productos y otros)
pueden estar registrados en el inventario. Cuando se venden, se crea
una SALIDA y se descuenta la existencia.

La relación es deliberadamente tolerante para trabajar con datos que ya
existen: primero intenta SKU/código de barras y después el nombre normalizado.
Si no encuentra una coincidencia inequívoca, no toca el inventario.
"""
import re
import unicodedata
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import InventoryItem, InventoryMovement
from app.modules.products.inventory_recipe_service import consume_product_recipe


def _key(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _name_variants(value: str | None) -> set[str]:
    key = _key(value)
    if not key:
        return set()
    variants = {key}
    # Permite "chorizo" <-> "chorizos" sin hacer coincidencias difusas
    # peligrosas entre productos diferentes.
    if len(key) > 4 and key.endswith("s"):
        variants.add(key[:-1])
    else:
        variants.add(key + "s")
    return variants


def find_inventory_item(db: Session, source) -> InventoryItem | None:
    """Encuentra un único artículo de inventario asociado a una venta."""
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.active.is_(True))
        .all()
    )

    source_code = getattr(source, "code", None)
    if source_code:
        code = str(source_code).strip()
        matches = [
            item for item in items
            if code and code in {str(item.sku or "").strip(), str(item.barcode or "").strip()}
        ]
        if len(matches) == 1:
            return matches[0]

    source_variants = _name_variants(getattr(source, "name", None))
    if not source_variants:
        return None

    matches = [
        item for item in items
        if source_variants.intersection(_name_variants(item.name))
    ]
    return matches[0] if len(matches) == 1 else None


def consume_for_sale(
    db: Session,
    source,
    quantity: int | float,
    *,
    order_id=None,
    reason_prefix: str = "Venta automática",
) -> InventoryItem | None:
    """
    Descuenta el inventario de un artículo vendido y registra SALIDA.

    Si el artículo no está registrado en inventario, no hace nada.
    Si sí está registrado pero no hay existencia suficiente, bloquea la venta
    para evitar que el inventario quede inconsistente.
    """
    if hasattr(source, "id") and source.__class__.__name__ == "Product":
        if consume_product_recipe(db, source, quantity, order_id=order_id):
            return source
    item = find_inventory_item(db, source)
    if not item:
        return None

    qty = Decimal(str(quantity))
    current = Decimal(str(item.quantity or 0))
    if qty <= 0:
        return None

    if current < qty:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Inventario insuficiente para '{item.name}'. "
                f"Disponible: {current:g} {item.unit}; solicitado: {qty:g}."
            ),
        )

    item.quantity = current - qty
    short_order = str(order_id)[:8].upper() if order_id else "SIN-COMANDA"
    reason = f"{reason_prefix} · Comanda {short_order} · {source.name}"

    db.add(
        InventoryMovement(
            item_id=item.id,
            movement_type="SALIDA",
            quantity=qty,
            reason=reason,
        )
    )
    return item
