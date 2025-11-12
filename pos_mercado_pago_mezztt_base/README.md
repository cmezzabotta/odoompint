# POS Mercado Pago QR (_mezztt) Base

Este módulo es la base para la integración de Mercado Pago QR en el POS de Odoo.

## Instrucciones

1. Colocar el módulo en `addons/` o `custom_addons/`.
2. Actualizar lista de módulos y **instalarlo** desde Aplicaciones.
3. Verificar que la ruta `/mp/mezztt/test` responde con el texto de confirmación.
4. Este módulo aún **no realiza llamadas reales** a Mercado Pago.
5. Codex deberá agregar:
   - Conexión real con la API de Mercado Pago.
   - Popup dinámico con QR.
   - Polling y webhook de confirmación.
   - Uso de credenciales del método de pago “Mercado Pago (Pago Online)”.
