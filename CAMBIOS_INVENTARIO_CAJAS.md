# Actualización Criptonix: cajas + inventario

## 1. Cajas
La tarjeta de cada caja cerrada ahora muestra:
- Retirado hoy: suma de retiros asociados a esa caja.
- Cantidad de retiros.

El backend ya entrega `withdrawals` y `withdrawal_count` en `/api/cashier/admin-summary`, por lo que no se modifica la base de datos de cajas.

## 2. Inventario
Se agrega el módulo `/admin/inventory` y su API `/api/inventory`.

Permite registrar:
- nombre, SKU y código de barras
- categoría y tipo
- marca y presentación
- unidad y existencias
- mínimo, máximo y cantidad sugerida de reposición
- costo unitario y valor de existencia
- almacenamiento y ubicación exacta
- lote
- fecha de compra, apertura y vencimiento
- temperatura/condición de almacenamiento
- proveedor
- alérgenos/advertencias
- notas

También permite movimientos de ENTRADA, SALIDA, MERMA y AJUSTE y conserva un historial.

## 3. Alertas
El inventario calcula:
- OK
- POR AGOTARSE
- SIN STOCK
- REVISAR VENCIMIENTO (7 días o menos)
- VENCIDO

Para productos con vencimiento recomienda revisar fecha, lote y cadena de frío. Para stock bajo recomienda reposición.

## 4. Excel
El botón **Descargar informe Excel** genera tres hojas:
- Inventario
- Alertas
- Movimientos

## Instalación
Desde `backend` ejecutar:

```bash
alembic upgrade head
```

Si `openpyxl` no está instalado:

```bash
pip install -r requirements.txt
```

Después reiniciar FastAPI y abrir `/admin/inventory`.
