from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import UUID

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password
from app.modules.roles.model import Role
from app.modules.users.model import User
from app.modules.attendance.model import AttendanceProfile, AttendanceSchedule, AttendanceDevice, AttendanceRecord
from app.modules.attendance.schemas import (
    AttendanceAdjustment,
    AttendanceCheckRequest,
    DeviceApproveRequest,
    DeviceRegisterRequest,
    DeviceStatusRequest,
    ScheduleUpdate,
    UserCreateAdmin,
    UserUpdateAdmin,
)

router = APIRouter(prefix="/api/attendance", tags=["Asistencia"])
admin_router = APIRouter(prefix="/api/admin", tags=["Administración - Usuarios y Asistencia"])

try:
    TZ = ZoneInfo("America/Bogota")
except Exception:
    # Windows puede no traer la base IANA instalada; Bogotá no usa horario de verano.
    TZ = timezone(timedelta(hours=-5))
WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def now_local() -> datetime:
    return datetime.now(TZ)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_admin(current_user=Depends(get_current_user)):
    if not current_user.role or current_user.role.name != "Administrador":
        raise HTTPException(status_code=403, detail="Solo un administrador puede realizar esta operación.")
    return current_user


def public_user(user: User, profile: AttendanceProfile | None = None):
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "active": user.is_active,
        "role": user.role.name if user.role else None,
        "attendance_enabled": bool(profile and profile.active),
    }


def get_or_create_profile(db: Session, user: User, pin: str | None = None) -> AttendanceProfile:
    profile = db.query(AttendanceProfile).filter(AttendanceProfile.user_id == user.id).first()
    if not profile:
        if not pin:
            pin = f"{secrets.randbelow(900000) + 100000}"
        profile = AttendanceProfile(
            user_id=user.id,
            qr_token=secrets.token_urlsafe(24),
            pin_hash=hash_password(pin),
            active=True,
        )
        db.add(profile)
        db.flush()
    elif pin:
        profile.pin_hash = hash_password(pin)
        profile.active = True
    return profile


def schedule_for(profile: AttendanceProfile | None, weekday: int):
    if not profile:
        return None
    return next((s for s in profile.schedules if s.weekday == weekday and s.enabled and s.start_time and s.end_time), None)


def minutes_between(a: datetime, b: datetime) -> int:
    return max(0, int((b - a).total_seconds() // 60))


def record_payload(record: AttendanceRecord | None, user: User, profile: AttendanceProfile | None = None):
    return {
        "id": str(record.id) if record else None,
        "user_id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "entry_at": record.entry_at.isoformat() if record and record.entry_at else None,
        "exit_at": record.exit_at.isoformat() if record and record.exit_at else None,
        "entry_status": record.entry_status if record else "ABSENT",
        "exit_status": record.exit_status if record else "PENDING",
        "late_minutes": record.late_minutes if record else 0,
        "early_leave_minutes": record.early_leave_minutes if record else 0,
        "overtime_minutes": record.overtime_minutes if record else 0,
        "adjustment_minutes": record.adjustment_minutes if record else 0,
        "adjustment_reason": record.adjustment_reason if record else None,
        "attendance_enabled": bool(profile and profile.active),
    }


# ==========================================================
# DISPOSITIVO FÍSICO DE ASISTENCIA
# ==========================================================

@router.post("/devices/register")
def register_device(data: DeviceRegisterRequest, request: Request, db: Session = Depends(get_db)):
    device = db.query(AttendanceDevice).filter(AttendanceDevice.device_uuid == data.device_uuid).first()
    now = now_local()
    if device and device.status == "ACTIVE":
        device.last_seen_at = now
        device.last_ip = request.client.host if request.client else None
        fresh_token = secrets.token_urlsafe(32)
        device.device_token_hash = sha256(fresh_token)
        db.commit()
        return {"device_id": str(device.id), "status": "ACTIVE", "device_token": fresh_token, "message": "Este dispositivo ya está autorizado."}

    if not device:
        device = AttendanceDevice(device_uuid=data.device_uuid)
        db.add(device)

    device.name = data.name or device.name or "Terminal de asistencia"
    device.pairing_code = f"{secrets.randbelow(900000) + 100000}"
    device.pairing_expires_at = now + timedelta(minutes=15)
    device.status = "PENDING"
    device.last_seen_at = now
    device.last_ip = request.client.host if request.client else None
    device.user_agent = request.headers.get("user-agent", "")[:500]
    device_token_secret = secrets.token_urlsafe(32)
    # El navegador conserva el secreto; el servidor solo guarda su hash.
    # Ese mismo secreto se convierte en el token de la terminal cuando el admin la aprueba.
    device.device_token_hash = sha256(device_token_secret)
    db.commit()
    db.refresh(device)
    return {
        "device_id": str(device.id),
        "device_uuid": device.device_uuid,
        "status": "PENDING",
        "pairing_code": device.pairing_code,
        "pairing_secret": device_token_secret,
        "expires_at": device.pairing_expires_at.isoformat(),
    }


@router.post("/devices/status")
def device_status(data: DeviceStatusRequest, request: Request, db: Session = Depends(get_db)):
    device = db.query(AttendanceDevice).filter(AttendanceDevice.device_uuid == data.device_uuid).first()
    if not device:
        raise HTTPException(404, "Dispositivo no registrado.")

    if device.device_token_hash != sha256(data.device_secret):
        raise HTTPException(403, "Credenciales del dispositivo no válidas.")
    if device.status == "PENDING" and device.pairing_expires_at and device.pairing_expires_at < now_local():
        raise HTTPException(410, "El código de emparejamiento expiró. Recarga esta terminal para generar uno nuevo.")

    if device.status == "ACTIVE":
        device.last_seen_at = now_local()
        device.last_ip = request.client.host if request.client else None
        db.commit()
        return {"status": "ACTIVE", "device_token": data.device_secret, "message": "Dispositivo autorizado."}

    return {
        "status": device.status,
        "pairing_code": device.pairing_code,
        "expires_at": device.pairing_expires_at.isoformat() if device.pairing_expires_at else None,
        "message": "Pendiente de autorización por el administrador.",
    }


@admin_router.get("/attendance/devices")
def list_devices(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AttendanceDevice).order_by(AttendanceDevice.status.asc(), AttendanceDevice.created_at.desc()).all()
    return [{
        "id": str(d.id), "name": d.name or "Terminal de asistencia", "status": d.status,
        "pairing_code": d.pairing_code, "created_at": d.created_at.isoformat() if d.created_at else None,
        "approved_at": d.approved_at.isoformat() if d.approved_at else None,
        "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
        "last_ip": d.last_ip,
    } for d in rows]


@admin_router.post("/attendance/devices/{device_id}/approve")
def approve_device(device_id: UUID, data: DeviceApproveRequest, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    device = db.query(AttendanceDevice).filter(AttendanceDevice.id == device_id).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado.")
    if not device.device_token_hash:
        raise HTTPException(409, "El dispositivo no tiene un secreto de emparejamiento válido. Regístrelo nuevamente.")
    device.status = "ACTIVE"
    device.name = data.name.strip()
    device.approved_at = now_local()
    device.pairing_code = None
    device.pairing_expires_at = None
    db.commit()
    return {"ok": True, "device_id": str(device.id)}


@admin_router.post("/attendance/devices/{device_id}/revoke")
def revoke_device(device_id: UUID, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    device = db.query(AttendanceDevice).filter(AttendanceDevice.id == device_id).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado.")
    device.status = "REVOKED"
    device.device_token_hash = None
    db.commit()
    return {"ok": True}


# ==========================================================
# FICHAJE DESDE LA TERMINAL
# ==========================================================

@router.post("/check")
def attendance_check(data: AttendanceCheckRequest, request: Request, db: Session = Depends(get_db)):
    device = db.query(AttendanceDevice).filter(
        AttendanceDevice.device_token_hash == sha256(data.device_token),
        AttendanceDevice.status == "ACTIVE",
    ).first()
    if not device:
        raise HTTPException(403, "Esta terminal no está autorizada para registrar asistencia.")

    profile = db.query(AttendanceProfile).filter(
        AttendanceProfile.qr_token == data.qr_token,
        AttendanceProfile.active == True,
    ).first()
    if not profile:
        raise HTTPException(404, "QR de empleado no válido o desactivado.")
    if not verify_password(data.pin, profile.pin_hash):
        raise HTTPException(401, "Código de acceso incorrecto.")

    user = db.query(User).options(joinedload(User.role)).filter(User.id == profile.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(404, "Empleado no disponible.")

    now = now_local()
    work_date = datetime.combine(now.date(), time.min, tzinfo=TZ)
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == user.id,
        AttendanceRecord.work_date == work_date,
    ).first()

    schedule = schedule_for(profile, now.weekday())
    if not record:
        record = AttendanceRecord(user_id=user.id, device_id=device.id, work_date=work_date)
        db.add(record)
        record.entry_at = now
        if schedule:
            scheduled = datetime.combine(now.date(), schedule.start_time, tzinfo=TZ)
            tolerance = scheduled + timedelta(minutes=schedule.tolerance_minutes)
            if now > tolerance:
                record.entry_status = "LATE"
                record.late_minutes = minutes_between(scheduled, now)
            else:
                record.entry_status = "ON_TIME"
        else:
            record.entry_status = "NO_SCHEDULE"
        action = "ENTRADA"
    elif record.entry_at and not record.exit_at:
        record.exit_at = now
        if schedule:
            scheduled_end = datetime.combine(now.date(), schedule.end_time, tzinfo=TZ)
            if now < scheduled_end:
                record.exit_status = "EARLY_EXIT"
                record.early_leave_minutes = minutes_between(now, scheduled_end)
            elif now > scheduled_end:
                record.exit_status = "OVERTIME"
                record.overtime_minutes = minutes_between(scheduled_end, now)
            else:
                record.exit_status = "ON_TIME"
        else:
            record.exit_status = "NO_SCHEDULE"
        action = "SALIDA"
    else:
        raise HTTPException(409, "La asistencia de hoy ya tiene entrada y salida registradas.")

    device.last_seen_at = now
    device.last_ip = request.client.host if request.client else None
    db.commit()
    return {
        "ok": True,
        "action": action,
        "message": f"{action.title()} registrada correctamente.",
        "employee": user.full_name,
        "time": now.strftime("%I:%M:%S %p"),
        "entry_status": record.entry_status,
        "exit_status": record.exit_status,
        "late_minutes": record.late_minutes,
        "early_leave_minutes": record.early_leave_minutes,
        "overtime_minutes": record.overtime_minutes,
    }


# ==========================================================
# USUARIOS / EMPLEADOS
# ==========================================================

@admin_router.get("/users")
def list_users(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).options(joinedload(User.role), joinedload(User.attendance_profile)).order_by(User.full_name.asc()).all()
    return [public_user(u, u.attendance_profile) for u in users]


@admin_router.get("/roles")
def list_roles(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    roles = db.query(Role).order_by(Role.name.asc()).all()
    return [{"id": str(r.id), "name": r.name, "description": r.description} for r in roles]


@admin_router.post("/users")
def create_user(data: UserCreateAdmin, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Ya existe un usuario con ese correo.")
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(404, "Rol no encontrado.")
    user = User(full_name=data.full_name.strip(), email=email, password=hash_password(data.password), role_id=role.id, is_active=data.active)
    db.add(user)
    db.flush()
    profile = None
    generated_pin = None
    attendance_pin = data.attendance_pin
    if data.attendance_enabled and role.name != "Cliente":
        if not attendance_pin:
            attendance_pin = f"{secrets.randbelow(900000) + 100000}"
            generated_pin = attendance_pin
        profile = get_or_create_profile(db, user, attendance_pin)
    db.commit()
    db.refresh(user)
    return {"user": public_user(user, profile), "qr_token": profile.qr_token if profile else None, "pin_generated": bool(generated_pin), "attendance_pin": generated_pin or data.attendance_pin}


@admin_router.patch("/users/{user_id}")
def update_user(user_id: UUID, data: UserUpdateAdmin, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role), joinedload(User.attendance_profile)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")
    if data.email:
        email = data.email.lower().strip()
        existing = db.query(User).filter(User.email == email, User.id != user.id).first()
        if existing:
            raise HTTPException(409, "Ese correo ya pertenece a otro usuario.")
        user.email = email
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.active is not None:
        user.is_active = data.active
    if data.role_id is not None:
        role = db.query(Role).filter(Role.id == data.role_id).first()
        if not role:
            raise HTTPException(404, "Rol no encontrado.")
        user.role_id = role.id
        db.flush()
    profile = user.attendance_profile
    if data.attendance_enabled is True and user.role and user.role.name != "Cliente":
        profile = get_or_create_profile(db, user, data.attendance_pin)
    elif data.attendance_enabled is False and profile:
        profile.active = False
    elif data.attendance_enabled is True and profile and data.attendance_pin:
        profile.pin_hash = hash_password(data.attendance_pin)
        profile.active = True
    db.commit()
    db.refresh(user)
    return {"user": public_user(user, profile), "qr_token": profile.qr_token if profile else None}


@router.get("/qr/user/{user_id}.svg")
def public_user_qr_svg(user_id: UUID, db: Session = Depends(get_db)):
    profile = db.query(AttendanceProfile).filter(AttendanceProfile.user_id == user_id, AttendanceProfile.active == True).first()
    if not profile:
        raise HTTPException(404, "QR de asistencia no disponible.")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(f"ELIMPERIO|EMP|{profile.qr_token}")
    qr.make(fit=True)
    matrix = qr.get_matrix()
    size = len(matrix)
    cells = []
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                cells.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="white"/>{"".join(cells)}</svg>'
    return Response(content=svg, media_type="image/svg+xml")


@admin_router.get("/users/{user_id}/qr.svg")
def user_qr_svg(user_id: UUID, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    profile = db.query(AttendanceProfile).filter(AttendanceProfile.user_id == user_id, AttendanceProfile.active == True).first()
    if not profile:
        raise HTTPException(404, "Este usuario no tiene asistencia habilitada.")
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(f"ELIMPERIO|EMP|{profile.qr_token}")
    qr.make(fit=True)
    matrix = qr.get_matrix()
    size = len(matrix)
    cells = []
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                cells.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="white"/>{"".join(cells)}</svg>'''
    return Response(content=svg, media_type="image/svg+xml")


# ==========================================================
# HORARIOS Y PANEL DE ASISTENCIA
# ==========================================================

@admin_router.get("/attendance/users/{user_id}/schedule")
def get_schedule(user_id: UUID, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    profile = db.query(AttendanceProfile).filter(AttendanceProfile.user_id == user_id).first()
    rows = db.query(AttendanceSchedule).filter(AttendanceSchedule.profile_id == profile.id).order_by(AttendanceSchedule.weekday.asc()).all() if profile else []
    result = []
    by_day = {r.weekday: r for r in rows}
    for day in range(7):
        r = by_day.get(day)
        result.append({"weekday": day, "name": WEEKDAYS[day], "enabled": bool(r and r.enabled), "start_time": r.start_time.strftime("%H:%M") if r and r.start_time else "", "end_time": r.end_time.strftime("%H:%M") if r and r.end_time else "", "tolerance_minutes": r.tolerance_minutes if r else 5})
    return result


@admin_router.put("/attendance/users/{user_id}/schedule")
def update_schedule(user_id: UUID, data: ScheduleUpdate, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")
    profile = get_or_create_profile(db, user)
    for item in data.schedules:
        row = db.query(AttendanceSchedule).filter(AttendanceSchedule.profile_id == profile.id, AttendanceSchedule.weekday == item.weekday).first()
        if not row:
            row = AttendanceSchedule(profile_id=profile.id, weekday=item.weekday)
            db.add(row)
        row.enabled = item.enabled
        row.start_time = item.start_time
        row.end_time = item.end_time
        row.tolerance_minutes = item.tolerance_minutes
    db.commit()
    return {"ok": True}


@admin_router.get("/attendance/today")
def attendance_today(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    now = now_local()
    day_start = datetime.combine(now.date(), time.min, tzinfo=TZ)
    records = db.query(AttendanceRecord).options(joinedload(AttendanceRecord.user).joinedload(User.role)).filter(AttendanceRecord.work_date == day_start).all()
    by_user = {r.user_id: r for r in records}
    staff = db.query(User).options(joinedload(User.role), joinedload(User.attendance_profile)).filter(User.is_active == True).all()
    rows = []
    for u in staff:
        if not u.role or u.role.name == "Cliente":
            continue
        rows.append(record_payload(by_user.get(u.id), u, u.attendance_profile))
    rows.sort(key=lambda x: (x["entry_at"] is None, x["name"].lower()))
    return {"date": now.date().isoformat(), "rows": rows}


@admin_router.get("/attendance/history")
def attendance_history(date_value: str | None = None, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    try:
        selected = date.fromisoformat(date_value) if date_value else now_local().date()
    except ValueError:
        raise HTTPException(400, "Fecha inválida.")
    day_start = datetime.combine(selected, time.min, tzinfo=TZ)
    rows = db.query(AttendanceRecord).options(joinedload(AttendanceRecord.user).joinedload(User.role)).filter(AttendanceRecord.work_date == day_start).order_by(AttendanceRecord.entry_at.asc().nullslast()).all()
    return {"date": selected.isoformat(), "rows": [record_payload(r, r.user) for r in rows]}


@admin_router.post("/attendance/adjustment")
def attendance_adjustment(data: AttendanceAdjustment, current_user=Depends(require_admin), db: Session = Depends(get_db)):
    day_start = datetime.combine(data.work_date, time.min, tzinfo=TZ)
    record = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == data.user_id, AttendanceRecord.work_date == day_start).first()
    if not record:
        record = AttendanceRecord(user_id=data.user_id, work_date=day_start)
        db.add(record)
    record.adjustment_minutes = (record.adjustment_minutes or 0) + data.adjustment_minutes
    record.adjustment_reason = data.reason.strip()
    record.adjusted_by = current_user.id
    db.commit()
    return {"ok": True, "adjustment_minutes": record.adjustment_minutes}
