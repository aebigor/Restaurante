from sqlalchemy.orm import Session

from .model import Station


class StationRepository:

    def __init__(self, db: Session):

        self.db = db


    def get_all(self):

        return (

            self.db

            .query(Station)

            .filter(Station.active == True)

            .order_by(Station.name)

            .all()

        )


    def get_by_name(self, name: str):

        return (

            self.db

            .query(Station)

            .filter(

                Station.name == name

            )

            .first()

        )


    def create(self, station: Station):

        self.db.add(station)

        self.db.commit()

        self.db.refresh(station)

        return station