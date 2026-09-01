from app.core.database import SessionLocal
from app.modules.users.model import User
from app.core.security import hash_password


db = SessionLocal()

email = "admin@criptonix.com"

user = db.query(User).filter(User.email == email).first()

if user:

    print("El administrador ya existe.")

else:

    admin = User(
        full_name="Administrador",
        email=email,
        password=hash_password("Admin123*"),
        is_active=True,
    )

    db.add(admin)
    db.commit()

    print("Administrador creado correctamente.")