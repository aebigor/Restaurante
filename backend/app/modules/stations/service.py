from fastapi import HTTPException
from sqlalchemy import func
from .model import Station
from .repository import StationRepository
from .schemas import StationCreate


class StationService:
    def __init__(self, db):
        self.db = db
        self.repository = StationRepository(db)

    def list(self):
        return self.repository.get_all()

    def create(self, data: StationCreate):
        exists = self.repository.get_by_name(data.name)
        if exists:
            raise HTTPException(status_code=400, detail="La estación ya existe.")

        max_priority = self.db.query(func.max(Station.priority)).scalar()
        priority = (max_priority or 0) + 1

        station = Station(
            name=data.name.strip(),
            description=data.description,
            printer_name=data.printer_name,
            color=data.color,
            priority=priority,
            auto_print=data.auto_print,
            sound_notification=data.sound_notification,
            accepts_delivery=data.accepts_delivery,
            supports_queue=data.supports_queue,
            active=True,
        )
        return self.repository.create(station)


    def update(self, station_id, data):
        station = self.db.query(Station).filter(Station.id == station_id, Station.active == True).first()
        if not station:
            raise HTTPException(status_code=404, detail="Estación no encontrada.")
        duplicate = self.db.query(Station).filter(
            Station.name == data.name.strip(), Station.id != station_id
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Ya existe otra estación con ese nombre.")
        for key, value in data.model_dump().items():
            setattr(station, key, value)
        self.db.commit(); self.db.refresh(station)
        return station

    def delete(self, station_id):
        station = self.db.query(Station).filter(Station.id == station_id, Station.active == True).first()
        if not station:
            raise HTTPException(status_code=404, detail="Estación no encontrada.")
        station.active = False
        self.db.commit()
        return {"ok": True}
