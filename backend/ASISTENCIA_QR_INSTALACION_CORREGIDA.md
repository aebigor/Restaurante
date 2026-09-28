# Asistencia QR - instalación corregida

Este paquete integra el módulo de asistencia con:

- Usuarios administrados desde `/admin/users`.
- QR individual + PIN de asistencia.
- Horario configurable por día y tolerancia.
- Terminal `/asistencia` que debe ser autorizada por el administrador.
- Entrada/salida, tardanza, salida anticipada y horas extra.
- Ajustes de minutos con motivo y administrador.
- Panel `/admin/attendance`.
- Configuración Gemini incluida en `app/core/config.py`.

## Instalación Windows

1. Detén Uvicorn/FastAPI y cualquier proceso Python que esté usando el entorno virtual.
2. Activa el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Instala dependencias:

```powershell
python -m pip install -r backend\requirements.txt
```

4. Verifica configuración:

```powershell
python -c "import sys; sys.path.insert(0, 'backend'); from app.core.config import settings; print('CONFIG OK:', settings.GEMINI_MODEL)"
```

5. Ejecuta migraciones desde `backend`:

```powershell
cd backend
alembic upgrade head
```

## Si aparece WinError 5 con psycopg2

Ese error significa que Windows tiene cargado `_psycopg*.pyd`. Detén Uvicorn/FastAPI, cierra las terminales que ejecuten el ERP y vuelve a ejecutar el `pip install`.

No borres `.venv` ni la base de datos por ese error.
