# Asistente conversacional gratuito

El bot puede usar Gemini mediante su API sin instalar un SDK adicional. Si no configuras la clave, mantiene el motor local de respaldo.

En `.env` agrega:

```env
GEMINI_API_KEY=TU_CLAVE
GEMINI_MODEL=gemini-3.8-flash
```

La clave se usa únicamente en el backend; nunca se envía al navegador.

La carta se consulta primero desde PostgreSQL y se entrega como contexto al modelo para evitar que invente precios o platos.
