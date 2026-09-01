from datetime import datetime

from fastapi import HTTPException

from app.modules.tables.repository import TableRepository

from .model import Session





class SessionService:

    def create(self, db, data, current_user):
        
        table_repository = TableRepository()

        table = table_repository.get_by_number(
            db,
            data.table_number
        )

        if table is None:

            raise HTTPException(
                status_code=404,
                detail="La mesa no existe."
            )

        existing = db.query(Session).filter(Session.table_id == table.id, Session.status == "OPEN").first()
        if existing:
            raise HTTPException(status_code=400, detail="La mesa ya está ocupada.")

        session = Session(

            table_id=table.id,

            waiter_id=current_user.id,

            people=data.people,

            status="OPEN",

            opened_at=datetime.now()

        )

        db.add(session)

        db.commit()

        db.refresh(session)

        return session