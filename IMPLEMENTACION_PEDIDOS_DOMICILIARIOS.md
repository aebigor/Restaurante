# Actualización — pedidos, domiciliarios, comprobantes y arqueo

## Incluye
- Presencia del domiciliario: heartbeat mientras el panel esté abierto y estado en línea/offline.
- Ubicación GPS visible para Caja y Administración.
- Vista global de domiciliarios contratados en Administración, con destino del pedido activo.
- Chat de soporte por pedido entre Caja y domiciliario.
- Flujo de cobro para el domiciliario después de validar el código del cliente.
- Reporte de efectivo/tarjeta o transferencia.
- Fotos de comprobantes para Nequi, Bancolombia y Llaves.
- Revisión y aprobación/rechazo del comprobante desde Caja.
- Cierre de la venta de domicilio como `CashPayment`, para que entre al arqueo de la caja.
- Reconciliación diaria de transferencias en Control de cajas.

## Instalación
1. Reemplaza los archivos del ZIP respetando sus rutas.
2. Desde `backend`, ejecuta:
   `alembic upgrade head`
3. Reinicia FastAPI.
4. Haz `Ctrl + F5` en las páginas de Caja, Administración y Domiciliario.

No se agregaron dependencias nuevas: el proyecto ya incluye `python-multipart`.

## Flujo esperado
1. Caja confirma el pedido y cocina lo prepara.
2. Domiciliario toma el pedido y comparte GPS.
3. Cliente entrega el código al domiciliario; la entrega pasa a pendiente de cobro.
4. Domiciliario informa el método. Para Nequi/Bancolombia/Llaves sube la foto.
5. Caja recibe el comprobante, lo revisa y lo aprueba.
6. Caja registra el pago y cierra la venta; la venta queda en la caja abierta.
7. Control de cajas muestra las transferencias por entidad y los comprobantes del día.

Para efectivo no se exige comprobante fotográfico: el cierre se realiza bajo la confirmación del personal, como se solicitó.
