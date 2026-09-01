from sqlalchemy.orm import Session

from .model import Session as TableSession


class SessionRepository:

    def create(self, db: Session, session: TableSession):

        db.add(session)

        db.commit()

        db.refresh(session)

        return session


    def get_open(self, db: Session):

        return db.query(TableSession).filter(
            TableSession.status == "OPEN"
        ).all()