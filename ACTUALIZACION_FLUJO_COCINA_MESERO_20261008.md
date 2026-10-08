# Flujo definitivo TV Cocina → Mesero

## Objetivo

La TV de cada estación funciona como una cola FIFO de preparación. Solo muestra trabajo pendiente de pedidos activos. Los registros antiguos/entregados quedan en historial y no regresan a la TV.

## Flujo

1. Mesero crea la comanda.
2. El producto entra a la estación correspondiente y aparece en la TV por `created_at ASC`.
3. Cocina prepara sin tener que pulsar "Tomar pedido".
4. Cuando termina, cocina pulsa `✓ LISTO PARA EL MESERO`.
5. La cola pasa a `READY`, desaparece de la TV y el mesero recibe sonido + aviso visible (y notificación del navegador si está permitida).
6. En el panel del mesero aparece `✓ Entregar al cliente`.
7. Al entregar, el producto pasa a `SERVED` y queda fuera de la operación activa. El historial conserva la comanda.

## Filtro de la TV

La TV solo consulta:
- `KitchenQueue.status IN (WAITING, PREPARING)`
- `OrderItem.status IN (PENDING, PREPARING)`
- `Order.served_at IS NULL`
- `Order.status IN (OPEN, PREPARING, READY)`
- `RestaurantSession.status = OPEN`

Por eso una comanda vieja, servida, cerrada o de una sesión cerrada no vuelve a aparecer.

## Cambios

- No requiere migración de Alembic.
- Se mantiene el historial de cocina.
- El mesero ya no tiene el botón `Marcar listo`.
- El mesero solo entrega cuando cocina marca `READY`.
- Se agregó polling de pedidos activos cada 2 segundos para detectar rápidamente el aviso de cocina.
