from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password

from app.modules.roles.model import Role
from app.modules.users.model import User


db: Session = SessionLocal()


# =====================================================
# CREAR ROL
# =====================================================

def create_role(
    name: str,
    description: str
):

    role = db.query(Role).filter(
        Role.name == name
    ).first()

    if role:

        print(f"✔ Rol {name} ya existe")

        return role

    role = Role(

        name=name,

        description=description,

       

    )

    db.add(role)

    db.commit()

    db.refresh(role)

    print(f"✔ Rol {name} creado")

    return role


# =====================================================
# CREAR USUARIO
# =====================================================

def create_user(

    full_name,

    email,

    password,

    role

):

    user = db.query(User).filter(

        User.email == email

    ).first()

    if user:

        print(f"✔ Usuario {email} ya existe")

        return

    nuevo = User(

        full_name=full_name,

        email=email,

        password=hash_password(password),

        role_id=role.id,


    )

    db.add(nuevo)

    db.commit()

    db.refresh(nuevo)

    print(f"✔ Usuario {email} creado")


# =====================================================
# ROLES
# =====================================================

admin_role = create_role(

    "Administrador",

    "Control total del restaurante"

)

mesero_role = create_role(

    "Mesero",

    "Gestiona pedidos"

)

cocina_role = create_role(

    "Cocina",

    "Visualiza y prepara pedidos"

)

caja_role = create_role(

    "Caja",

    "Realiza cobros"

)


# =====================================================
# USUARIOS INICIALES
# =====================================================

create_user(

    "Administrador",

    "admin@imperio.com",

    "admin123",

    admin_role

)

create_user(

    "Mesero Principal",

    "mesero1@imperio.com",

    "admin123",

    mesero_role

)

create_user(

    "Cocinero",

    "cocina@imperio.com",

    "admin123",

    cocina_role

)

create_user(

    "Cajero",

    "caja@imperio.com",

    "admin123",

    caja_role

)


print("\n===================================")
print(" Sistema inicial creado correctamente")
print("===================================\n")

db.close()