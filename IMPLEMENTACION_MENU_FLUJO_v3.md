# Restaurante - Flujo v3

## Cambios principales

### Base de datos / estaciones
- `Station` ahora refleja las columnas existentes de la migración inicial, incluyendo `priority`.
- La prioridad se calcula automáticamente al crear una estación (`MAX(priority) + 1`).
- Se agregó una migración segura `9a3f6b2c1d44_station_priority_alignment.py`.
- No se elimina la columna `priority` ni se modifica la restricción NOT NULL.

### Configuración del menú
- Una categoría nueva requiere una estación de cocina.
- Un plato usa la estación de su categoría.
- El backend valida que `dish.station_id == category.station_id`.
- El formulario del plato muestra la estación como dato automático.

### Mesero
- `/waiter` muestra mesas y solicitudes de llamado.
- Las mesas se consultan con las sesiones abiertas, no con una columna `status` inexistente.
- El mesero abre/recupera una sesión.
- Puede seleccionar platos, cantidades y enviar una comanda.
- Al enviar una comanda, el backend la divide automáticamente por estación.
- Se crean `OrderBatch`, `KitchenTicket` y `KitchenQueue` para cada estación/item.

### KDS
- `/kitchen/{screen_code}` funciona como pantalla de una estación.
- Cada pantalla está vinculada a una estación.
- El administrador puede abrir/preparar una pantalla desde Centro de Cocina.
- El KDS muestra mesa, comanda, plato, cantidad, estado y cronómetro.
- Estados: WAITING -> PREPARING -> READY.
- Se registra heartbeat de pantalla.

### Prueba
1. Ejecutar `alembic upgrade head`.
2. Iniciar el servidor.
3. Entrar como usuario con rol Mesero.
4. Crear una estación desde `/admin/kitchen`.
5. Crear una categoría y asignarle esa estación.
6. Crear platos de esa categoría.
7. En Centro de Cocina, abrir la pantalla de la estación.
8. Ir a `/waiter`, seleccionar una mesa, agregar platos y enviar.
9. La comanda aparecerá automáticamente en la pantalla KDS correspondiente.

Nota: la creación de sesión y pedidos del mesero está protegida por el token de autenticación existente.
