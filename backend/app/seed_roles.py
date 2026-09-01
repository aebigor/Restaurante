from app.core.database import SessionLocal
from app.modules.roles.model import Role

db = SessionLocal()

roles = [
    "Administrador",
    "Caja",
    "Mesero",
    "Cocina",
    "Parrilla",
    "Sopas",
]

for role in roles:

    existe = db.query(Role).filter(Role.name == role).first()

    if not existe:
        db.add(
            Role(
                name=role,
                description=role,
            )
        )

db.commit()

print("Roles creados.")