# Asistencia QR — El Imperio del Barril

Se agregó un módulo de control de asistencia pensado para una **terminal física autorizada** dentro del restaurante.

## Flujo

1. En **Administración → Usuarios** el administrador crea al empleado.
2. Se activa asistencia y se define un PIN personal.
3. Se imprime su tarjeta con QR.
4. En la tablet/computador del restaurante se abre `/asistencia`.
5. La primera vez la terminal muestra un código de emparejamiento.
6. En **Administración → Asistencia → Dispositivos** el administrador la autoriza.
7. El empleado escanea su QR y escribe su PIN.
8. El sistema registra entrada o salida.
9. El horario configurado permite detectar:
   - llegada tarde
   - salida temprana
   - horas extra
10. El administrador puede registrar ajustes de minutos para reposición, permisos o correcciones.

## Horarios

Cada empleado tiene una configuración independiente de lunes a domingo. Por ejemplo:

- Lunes a viernes: 06:00 → 18:00
- Sábado: 10:00 → 19:00
- Domingo: 10:00 → 19:00

La tolerancia también se puede modificar por día.

## Migración

Después de reemplazar los archivos:

```bash
cd ~/Restaurante/backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Luego reinicia el proceso de Uvicorn/FastAPI que utiliza el restaurante.

## Terminal física

La terminal debe quedarse en el restaurante. La autorización queda asociada al navegador/dispositivo mediante un identificador y un secreto almacenado localmente. Si se revoca desde administración, deja de poder fichar.

## Nota

El módulo está preparado para crecer después hacia reportes de nómina, acumulado de horas, ausencias, turnos e incidencias sin cambiar el concepto de fichaje.
