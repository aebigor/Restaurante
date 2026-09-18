# Cambios: cliente registrado, domicilios y seguimiento online

## Flujo nuevo

1. El cliente se registra en `/register`.
2. El registro crea la cuenta con rol `Cliente`, inicia sesión automáticamente y guarda la sesión en el navegador.
3. En la página principal, `Ingresar` desaparece y aparece un avatar circular con las iniciales, por ejemplo `SB`.
4. El cliente arma su carrito y pasa a `/checkout`.
5. Para `DOMICILIO` son obligatorios dirección y teléfono. El endpoint también lo valida en backend.
6. El pedido se crea con estado `PENDING_CASHIER`; todavía no entra a cocina.
7. Caja lo ve en la sección **Pedidos online**.
8. Caja pulsa **Confirmar y enviar a cocina**. En ese momento se crean las colas de cocina y el pedido pasa a `OPEN`.
9. Cocina lo toma y pasa a `PREPARING`; al terminar pasa a `READY`.
10. Para domicilio, Caja puede marcar **En camino** (`OUT_FOR_DELIVERY`) y posteriormente **Entregado / cerrado** (`DELIVERED`).
11. El cliente consulta `/mis-pedidos`, que se actualiza automáticamente cada 5 segundos.

## Migración

Después de actualizar el código, desde `backend` ejecutar:

```bash
alembic upgrade head
```

La migración `e1f4a8c9b7d2_customer_delivery_tracking.py` agrega a `orders` los datos necesarios para notas, dirección, teléfono y tiempos de confirmación/despacho.

## Estados online

- `PENDING_CASHIER`: recibido, esperando Caja.
- `OPEN`: Caja confirmó y lo envió a cocina.
- `PREPARING`: cocina está preparando.
- `READY`: pedido listo.
- `OUT_FOR_DELIVERY`: salió a domicilio.
- `DELIVERED`: entregado y cerrado.
- `CANCELLED`: cancelado.

El seguimiento usa consultas periódicas (polling) de 5 segundos, por lo que no requiere WebSocket para esta primera versión.
