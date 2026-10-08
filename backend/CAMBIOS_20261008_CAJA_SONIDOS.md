# Cambios 2026-10-08 — Caja, liberación de mesa y alertas sonoras

## Liberación desde Caja
- Caja puede liberar una mesa en estado `PAID` o `CLEAN`.
- La liberación no depende de que el mesero haya marcado `served_at`.
- Al liberar desde Caja, todas las órdenes no canceladas de la sesión pasan a `CLOSED` y la sesión pasa a `CLOSED`.
- El criterio operativo es: si Caja recibió el pago y autoriza "Liberar mesa", el consumo se considera finalizado.
- El mesero ya no libera mesas de pago anticipado; solo puede marcar la mesa como `CLEAN`.

## Alertas sonoras
- Cocina: cada estación emite un sonido cuando aparece una nueva comanda `WAITING` en su propia cola.
- Mesero: emite un sonido cuando llega una nueva solicitud de atención.
- Mesero: emite un sonido cuando aparece un pedido nuevo o cuando un producto pasa a `READY`.
- Se usa Web Audio API, sin archivos de audio externos.
- El primer clic/toque en la página habilita el audio para evitar el bloqueo de autoplay del navegador.

## Otros arreglos conservados
- Se agregó la vista `/admin/inventory`.
- Se agregó `Pillow>=11.0.0` a `requirements.txt` para que `qrcode` pueda generar imágenes PNG.

## Reinicio en servidor
Después de desplegar:

```bash
cd ~/Restaurante/backend
source ../venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart restaurante.service
sudo systemctl status restaurante.service --no-pager -l
```
