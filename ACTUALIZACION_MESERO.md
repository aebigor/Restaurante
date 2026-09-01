# Actualización módulo Mesero

Esta versión mejora el seguimiento de mesas y comandas sin cambiar las dependencias del proyecto.

## Cambios

- Una mesa ocupada puede recibir múltiples pedidos dentro de la misma sesión.
- Se muestra cuánto tiempo lleva ocupada la mesa.
- Se muestra cuánto tiempo hace que se realizó cada pedido.
- Cuando una comanda está completamente lista, el mesero puede imprimirla.
- El mesero puede marcar la comanda como entregada.
- Al entregar se guarda `served_at` y comienza el contador de tiempo comiendo.
- Se puede abrir un nuevo pedido para una mesa ocupada sin crear otra sesión.
- La mesa solo se libera al cerrar la sesión/cuenta, no al entregar una comanda.
- Se agregó validación para no cerrar una mesa si todavía hay pedidos sin entregar.

## Actualización de base de datos

No hay que instalar librerías nuevas.

Después de reemplazar el proyecto, ejecutar desde `backend`:

```bash
alembic upgrade head
```

La migración nueva agrega únicamente `orders.served_at`.

Si usas `uvicorn ... --reload`, reinicia el servidor si no detecta los cambios.
