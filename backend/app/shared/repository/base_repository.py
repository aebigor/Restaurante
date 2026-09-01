from sqlalchemy.orm import Session


class BaseRepository:

    def __init__(self, db: Session, model):

        self.db = db
        self.model = model

    def get_all(self):

        return self.db.query(self.model).all()

    def get_by_id(self, id):

        return (
            self.db.query(self.model)
            .filter(self.model.id == id)
            .first()
        )

    def create(self, obj):

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)

        return obj

    def update(self):

        self.db.commit()

    def delete(self, obj):

        self.db.delete(obj)
        self.db.commit()