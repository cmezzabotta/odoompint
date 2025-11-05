# POS Mercado Pago QR

Modulo para integrar el Punto de Venta de Odoo con cobros vía QR dinámico de Mercado Pago. Al validar un pedido con el método de pago configurado, el cajero verá un popup con el código QR y el sistema consultará periódicamente a Mercado Pago hasta confirmar el pago de forma automática.

## Requisitos previos

- Credenciales de una aplicación de Mercado Pago con acceso a la API de QR dinámicos (token de acceso, collector ID, POS externo y opcionalmente Store ID).
- Odoo 18 con los módulos `point_of_sale` y `pos_online_payment` instalados.
- Conexión HTTPS pública para recibir notificaciones (webhooks) desde Mercado Pago.

## Instalación

1. Copiar la carpeta `pos_mercado_pago_qr` dentro del `addons_path` de Odoo.
2. Reiniciar el servicio de Odoo para que detecte el nuevo módulo.
3. Activar el modo desarrollador y actualizar la lista de aplicaciones.
4. Instalar **POS Mercado Pago QR** desde Apps.

## Configuración del método de pago

1. Ir a **Punto de Venta → Configuración → Métodos de pago** y crear (o editar) un método de pago.
2. En el campo **Integración** seleccionar *Terminal* y, en **Usar terminal de pago**, elegir *Mercado Pago QR*.
3. Completar los campos del bloque Mercado Pago:
   - **Access Token**: Token privado `APP_USR-...` de Mercado Pago.
   - **Collector ID**: Identificador numérico del usuario/cuenta.
   - **External POS ID**: Código del punto de venta definido en Mercado Pago.
   - **Store ID** (opcional): Identificador de sucursal si se utiliza en la cuenta.
   - **QR validity (minutes)**: Tiempo que permanecerá vigente el QR dinámico (por defecto 10 minutos).
   - **Receipt message**: Mensaje adicional que se envía en la orden de Mercado Pago.
   - **Webhook Secret** (opcional): Clave utilizada para validar la firma `x-signature` de Mercado Pago.
4. Guardar el método de pago y asignarlo a la(s) configuración(es) de POS deseadas.

> El campo **Webhook URL** se completa automáticamente con la ruta pública que debe registrarse en el panel de desarrolladores de Mercado Pago para recibir notificaciones.

## Flujo de cobro en el POS

1. El cajero selecciona el método de pago *Mercado Pago QR* y presiona **Validar**.
2. El módulo crea una orden dinámica en Mercado Pago, muestra el QR en un popup y comienza a consultar el estado cada 4 segundos.
3. Al aprobarse el pago en la app del cliente, el pedido se valida automáticamente en Odoo.
4. Si el cliente cancela, expira el QR o el cajero cierra el popup, la orden se anula mediante la API de Mercado Pago.

Las notificaciones vía webhook (si están configuradas) también actualizan el estado de la orden en Odoo; el POS reflejará el cambio en el siguiente ciclo de verificación.

## Webhook de Mercado Pago

- URL: `https://TU_DOMINIO/mercado-pago/pos-qr/webhook`
- Método: `POST` (JSON)
- Validación opcional: si configurás un **Webhook Secret**, el módulo verificará la cabecera `x-signature` utilizando HMAC-SHA256.

Cuando se recibe un evento `payment.updated` o `order.updated` con un `external_reference` registrado, el estado de la orden se sincroniza y se avisa al POS correspondiente.

## Monitoreo de órdenes

El modelo técnico `pos.mercadopago.qr.order` guarda el historial de órdenes generadas (referencia, QR, estado, último payload recibido y sesión POS). Podés revisarlo desde **Punto de Venta → Informes → Órdenes Mercado Pago QR** (activa la lista desde el modo desarrollador si necesitás depurar).

## Solución de problemas

- **QR no se genera**: Verificá las credenciales (token, collector y POS ID) y que la cuenta tenga habilitada la API de QR dinámicos.
- **No se confirma el pago**: Revisá el log en Odoo (`mpqr_last_error`) y validá que la URL pública sea accesible. Si no usás webhooks, aumentá el tiempo de validez o revisá conectividad saliente.
- **Firma inválida**: Confirmá que el secret configurado en Mercado Pago coincida con el cargado en Odoo.

## Créditos

- **Autor**: Mezztt
- Basado en la API pública de Mercado Pago y en la arquitectura de pagos electrónicos del POS de Odoo.
