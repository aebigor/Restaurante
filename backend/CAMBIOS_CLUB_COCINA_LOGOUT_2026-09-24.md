# Cambios: Club del Imperio, cocina y cierres de sesión

## 1. Cliente registrado
- El bloque "Conviértete en cliente frecuente" se oculta automáticamente cuando hay una sesión de Cliente.
- En su lugar aparece "Promociones y combos para ti".
- Si el administrador no ha publicado nada, se muestra un estado vacío.
- La página reacciona también al evento de sincronización de sesión para evitar que el bloque de registro aparezca brevemente después de iniciar sesión.

## 2. Promociones y combos
Se agregó el módulo `/admin/promotions`.
El administrador puede:
- Crear promociones.
- Crear combos.
- Editarlos.
- Ocultarlos/eliminarlos.
- Definir precio, descripción, orden e imagen por URL.

Las promociones activas aparecen en el Club del Imperio para clientes registrados.

### Base de datos
Después de reemplazar el código, ejecutar dentro de `backend`:

```bash
alembic upgrade head
```

La nueva migración es `32c7d8e9f0a1_create_promotions.py`.

## 3. Cocina
En `/admin/kitchen` cada estación ahora tiene:
- Ver pantalla.
- Editar.
- Eliminar.

Eliminar es un borrado lógico: la estación pasa a `active=false`.

El botón "Nueva estación" conserva su función y el formulario cambia a "Guardar cambios" cuando se edita.

## 4. Cerrar sesión
Se revisaron los cierres de sesión de:
- Administrador.
- Caja.
- Domiciliario.
- Mesero.
- Cocina.
- Cliente.

Los roles internos eliminan solamente `token` y `user`, sin usar `localStorage.clear()`, para no borrar datos de otras sesiones del navegador.
