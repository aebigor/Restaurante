# Dashboard público - El Imperio del Barril

## Rutas

- `/` → dashboard público del cliente.
- `/login` → login de cliente / cuenta frecuente.
- `/register` → registro de cliente frecuente.
- `/admin/login` → login privado para personal administrativo.
- `/admin` → administración.
- `/waiter` → mesero.
- `/kitchen` → cocina.
- `/cashier` → caja.
- `/m/{mesa}` → menú QR por mesa existente.

## Rol Cliente

Se agregó `Cliente` a `app/seed_roles.py` y al `seed.py` principal.
Además, `/auth/register` crea automáticamente el rol `Cliente` si todavía no existe.

Si el proyecto ya está instalado, desde `backend` puedes ejecutar:

```bash
python app/seed_roles.py
```

## Menú dinámico

La página `/` consulta el menú activo de `menus` y únicamente muestra los `menu_items` activos asociados a ese menú. Por tanto, el administrador sigue controlando qué platos aparecen sin duplicar el sistema de menú.

## Carrito

El carrito funciona actualmente en frontend usando `localStorage`. El botón `CONTINUAR PEDIDO` guarda el pedido temporal y envía al login. La creación real de la orden se conectará en el siguiente paso con el flujo existente de mesa/sesión → cocina → caja.

## Mapa

La sección de ubicación contiene un espacio preparado para reemplazarlo posteriormente por Google Maps u OpenStreetMap, sin modificar la estructura del dashboard.
