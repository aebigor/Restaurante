from app.core.database import SessionLocal
from app.modules.permissions.model import Permission

db = SessionLocal()

permissions = [

    ("dashboard.view","Dashboard","dashboard"),

    ("inventory.view","Ver inventario","inventory"),
    ("inventory.edit","Editar inventario","inventory"),

    ("tables.view","Ver mesas","tables"),
    ("tables.create","Crear mesas","tables"),
    ("tables.edit","Editar mesas","tables"),

    ("orders.create","Crear pedidos","orders"),
    ("orders.edit","Editar pedidos","orders"),
    ("orders.cancel","Cancelar pedidos","orders"),

    ("kitchen.view","Ver cocina","kitchen"),
    ("kitchen.finish","Pedido listo","kitchen"),

    ("cashier.view","Ver caja","cashier"),
    ("cashier.pay","Cobrar","cashier"),
    ("cashier.close","Cerrar cuenta","cashier"),

    ("reports.view","Ver reportes","reports"),

]

for code,name,module in permissions:

    exists = db.query(Permission).filter(
        Permission.code == code
    ).first()

    if not exists:

        db.add(

            Permission(
                code=code,
                name=name,
                module=module,
            )

        )

db.commit()

print("Permisos creados correctamente.")