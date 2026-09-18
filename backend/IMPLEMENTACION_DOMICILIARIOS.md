# Implementación de Domiciliarios - El Imperio del Barril

## Flujo
Cliente -> Caja -> Cocina -> Listo -> Domiciliario -> Entregado pendiente de pago -> Caja cierra.

- Domicilio agrega una tarifa de $7.000 COP. Para recoger no se agrega.
- Cada domicilio genera un código de entrega de 6 dígitos. El cliente debe entregarlo al domiciliario.
- El domiciliario toma el pedido desde `/domiciliario`, recibe dirección y tiempos de cocina.
- El domiciliario puede cancelar una entrega indicando motivo.
- Al entregar, el domiciliario valida el código. El pedido queda `DELIVERED_PENDING_PAYMENT`.
- Caja registra CASH, CARD o TRANSFER (incluye Nequi/transferencia) y pasa el pedido a `CLOSED`.
- El domiciliario reporta ubicación GPS mientras la aplicación está abierta y el navegador haya dado permiso.
- Caja puede consultar las últimas ubicaciones de los domiciliarios.
- Se agregó mensajería básica entre Caja/Administrador/Domiciliarios mediante actualización periódica.
- La estructura deja `courier_id` y ubicación separadas para poder ampliar a múltiples tiendas posteriormente.

## Migración
Desde `backend`:

```powershell
alembic upgrade head
```

Nueva revisión: `f3b7c9d1e2a4`.

## Rol
Se agrega el rol `Domiciliario` al seed. Si el rol ya existe, el seed debe conservarlo según la lógica existente.
