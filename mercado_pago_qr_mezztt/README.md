# Mercado Pago QR (mezztt) para Odoo 18 POS

Este módulo convierte el prototipo de popup incluido en el repositorio en una integración real con el Punto de Venta moderno (OWL) de Odoo 18.  Permite operar con QR **estático** de Mercado Pago, pero detrás de escena crea órdenes reales mediante la API oficial de *In Store Orders*.

## Contenido del módulo

| Archivo | Descripción |
| --- | --- |
| `mp_config.py` / `static/src/js/mp_config.js` | Configuración centralizada de credenciales y URL del QR estático. Debe editarse manualmente por cada caja. |
| `controllers/main.py` | Endpoints HTTP que intermedian todas las llamadas a la API de Mercado Pago (crear orden, consultar estado y webhook). |
| `models/mp_order.py` | Almacena la relación entre el pedido del POS y la orden de Mercado Pago para depurar y sincronizar estados. |
| `static/src/xml/mercado_pago_popup.xml` | Popup OWL inspirado en el diseño original del repo. Muestra productos, total y QR estático. |
| `static/src/js/mercado_pago_popup.js` | Lógica del popup: creación de la orden, polling periódico, cierre automático tras la aprobación. |
| `static/src/js/mercado_pago_terminal.js` | Implementación del `PaymentTerminal` `mercado_pago_qr_mezztt`. Abre el popup cuando se elige el método de pago y valida la orden al aprobarse. |
| `data/pos_payment_method_data.xml` | Método de pago y terminal POS preconfigurados. |
| `security/ir.model.access.csv` | Permisos para consultar las órdenes registradas localmente. |

## Requisitos previos en Mercado Pago

1. **Crear la sucursal (branch)**
   - Ingresar al panel de Mercado Pago → *Configuraciones* → *Sucursales y Cajas*.
   - Generar una nueva sucursal para la heladería (por ejemplo `SUC01`).
   - Anotar el `branch_id` exacto si la cuenta lo utiliza.

2. **Crear la caja / punto de venta (POS)**
   - Dentro de la sucursal seleccionar *Crear caja*.
   - Elegir un nombre legible (ej. "Mostrador 1").
   - Mercado Pago asignará un `external_pos_id` (código alfanumérico).  Registrar el valor para `POS_ID`.

3. **Generar el QR estático**
   - En la misma caja hacer clic en *Crear código QR* → *Modo estático*.
   - Descargar la imagen PNG y copiar la URL pública provista por Mercado Pago.
   - Reemplazar `STATIC_QR_URL` en `mp_config.py` y `mp_config.js` con esa URL.

4. **Obtener credenciales**
   - Panel de Mercado Pago → *Tus integraciones* → *Credenciales*.
   - Copiar `access_token` (privada) y `public_key` (pública) del ambiente deseado.
   - Configurar `COLLECTOR_ID` con el identificador numérico de la cuenta.
   - Si Mercado Pago asigna identificadores de integrador (`integrator_id` / `platform_id`) o sponsor, completarlos en el config.

> ⚠️ Por seguridad **no** subir estas credenciales a repositorios públicos.  Reemplazar los placeholders solo en entornos privados.

## Flujo completo en el POS

1. Instalar el módulo y activar el método de pago *Mercado Pago QR* en las configuraciones del POS.
2. Iniciar una sesión POS, agregar productos y seleccionar el método de pago configurado.
3. El `PaymentTerminal` `mercado_pago_qr_mezztt` abre el popup estilo checkout.
   - Lista productos, cantidades y subtotal.
   - Muestra el total y el botón **Pagar**.
4. Al presionar **Pagar**:
   - El popup llama al endpoint `/mercado_pago_qr_mezztt/create_order`.
   - El controlador crea una orden real en Mercado Pago con `collector_id`, `pos_id`, `branch_id` y la referencia del pedido Odoo.
   - El backend almacena `mp_order_id` en el modelo `mercado.pago.qr.order`.
5. El popup cambia al estado **waiting** y muestra el QR estático indicado en `MP_CONFIG`.
6. Cada 3 segundos (configurable) se consulta `/mercado_pago_qr_mezztt/order_status/<order_id>`:
   - Si Mercado Pago devuelve `approved`, el popup muestra "Pago procesado", espera 5 segundos y cierra confirmando el pago.
   - Si devuelve `rejected`, informa el error y permite reintentar.
7. Al confirmarse el pago:
   - El PaymentTerminal marca la línea como pagada, valida el pedido en el POS y crea uno nuevo vacío listo para el siguiente cliente.
8. Mercado Pago puede enviar notificaciones al webhook `/mercado_pago_qr_mezztt/webhook`.
   - Siempre responde 200 OK.
   - Actualiza el estado en `mercado.pago.qr.order` para acelerar futuros pollings.

## Configuración en Odoo

1. Copiar el módulo dentro de la carpeta de addons y actualizar la lista de módulos.
2. Instalar **Mercado Pago QR for POS (mezztt)**.
3. Entrar en *Punto de Venta → Configuración → Métodos de pago* y habilitar **Mercado Pago QR** en la sesión deseada.
4. Editar `mp_config.py` y `static/src/js/mp_config.js` con los valores reales de la caja.
   - Reiniciar el servidor Odoo y reconstruir los assets del POS (`-u mercado_pago_qr_mezztt`) para que el frontend tome los cambios.

## Webhook

- Configurar la URL pública del servidor Odoo en el panel de Mercado Pago (por ejemplo `https://midominio.com/mercado_pago_qr_mezztt/webhook`).
- Mercado Pago enviará eventos `payment.updated` / `order.updated` con la información de la orden.
- El módulo guarda la última carga útil para facilitar auditorías.

## Pruebas recomendadas

1. Ejecutar una sesión de prueba con credenciales sandbox y confirmar que la orden aparece en el panel de Mercado Pago.
2. Validar que al aprobar el pago el pedido del POS se marque como pagado y se genere uno nuevo.
3. Revisar el modelo `mercado.pago.qr.order` desde *Técnico → Base de datos → Modelos* para confirmar que se registran los estados.

## Personalización del diseño

- El popup reutiliza los estilos del prototipo original, adaptados a clases prefijadas `mpq-*`.
- Para modificar colores o tamaños, editar `mercado_pago_qr_mezztt/static/src/xml/mercado_pago_popup.xml` y aplicar CSS desde un módulo complementario.

## Soporte y mantenimiento

- Cualquier cambio de caja requiere actualizar `MP_CONFIG` en ambos archivos.
- El `PaymentTerminal` está registrado con el nombre técnico `mercado_pago_qr_mezztt`; si se crea otro módulo con QR diferente, usar un nombre distinto para evitar colisiones.
- Mantener el token privado fuera de repositorios públicos y rotarlo periódicamente según las políticas de Mercado Pago.

¡Listo! Con estos pasos la heladería puede cobrar con un QR estático manteniendo la creación de órdenes en la cuenta oficial de Mercado Pago.
