# Actualización cliente: sesión y tiempos de domicilio

Se agregaron las funciones finales de seguimiento del cliente:

## 1. Cerrar sesión
- Botón `Cerrar sesión` en Mis pedidos.
- Botón de salida en el encabezado público cuando existe una sesión de cliente.
- Limpia `token`, `user`, carrito y pedido pendiente del navegador.

## 2. Tiempos del pedido
Se agregaron a `orders`:
- `kitchen_started_at`: inicio real de preparación.
- `ready_at`: momento en que todos los productos quedan listos.

Migración nueva:
- `f2a6b8c9d0e1_customer_order_timing.py`

## 3. Cálculo de llegada
La API de `GET /orders/customer` ahora devuelve:
- `elapsed_seconds`: tiempo transcurrido desde que se creó el pedido.
- `eta_min` / `eta_max`: ventana estimada de llegada.
- `estimated_arrival_at`: hora aproximada.

El cálculo usa pedidos a domicilio históricos ya entregados. Si todavía no hay suficiente historial, usa una estimación base que posteriormente se ajusta con los datos reales.

## 4. Cocina
Cuando Cocina inicia el primer producto de un pedido online se guarda `kitchen_started_at`.
Cuando todos los productos del pedido quedan listos se guarda `ready_at`.

## Aplicación de migración
Desde:

```powershell
cd C:\laragon\www\Restaurante\backend
alembic upgrade head
```

Debe quedar como cabeza:

```text
e1f4a8c9b7d2 -> f2a6b8c9d0e1
```

Luego reiniciar FastAPI.
