# Implementación v1 — Menú + operación del restaurante

Esta versión prepara el primer flujo conectado del restaurante.

## Incluido

- Creación de platos con imagen, precio, descripción, ingredientes, porción y tiempo.
- Botón de Modelo 3D deshabilitado para la futura IA.
- Imagen subida al backend y guardada en `app/static/uploads/dishes`.
- Categorías asociadas a una estación de cocina.
- El plato conserva la estación derivada de su categoría.
- Comandas: `OrderItem` acepta platos y crea automáticamente su lote y cola de cocina.
- Cola de cocina con estados `WAITING`, `PREPARING` y `READY`.
- Cronómetro por ítem desde recepción / inicio de preparación.
- Pantallas configurables por estación mediante el módulo `screens`.
- Menú público del cliente en `/m/{numero_mesa}`.
- El cliente no puede ordenar; solo puede consultar el menú y llamar al mesero.
- Registro de solicitud de mesero: `requested_at`, `acknowledged_at`, `attended_at`.
- Panel de mesero en `/waiter`.
- Pantalla KDS en `/kitchen/{screen_code}`.

## Migración

Después de copiar los archivos, conservar el `.env` de tu instalación y ejecutar:

```bash
cd backend
alembic upgrade head
```

Luego iniciar normalmente:

```bash
python ../run.py
```

## Primer flujo de prueba

1. Crear estaciones: Cocina Principal, Picadas, Bebidas, etc.
2. Crear categorías y asignar cada categoría a una estación.
3. Crear platos; la estación se completa automáticamente desde la categoría.
4. Crear una pantalla con un `code`, por ejemplo `TV-PICADAS-01`, asociada a la estación de Picadas.
5. Abrir `/kitchen/TV-PICADAS-01` en el televisor.
6. Abrir `/waiter` en el dispositivo del mesero.
7. Abrir `/m/1` para el menú de la mesa 1.
8. Desde el menú público, pulsar `Llamar al mesero` y verificar que la solicitud aparece en `/waiter`.

La siguiente iteración debe conectar la vista completa del mesero con mesas, sesiones, creación de comanda y envío de múltiples platos, además de mejorar la administración visual de estaciones y pantallas.
