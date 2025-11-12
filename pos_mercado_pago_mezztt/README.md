# POS Mercado Pago QR (_mezztt)

Este módulo agrega una terminal de pago para el Punto de Venta de Odoo
(Odoo 16+) que permite cobrar mediante códigos QR dinámicos generados por
Mercado Pago. El flujo se apoya en la configuración existente del método de
pago "Mercado Pago (Pago Online)" y en credenciales fijas asociadas a la
caja/terminal.

## Instalación

1. Copiar el directorio `pos_mercado_pago_mezztt` dentro de la carpeta de
   `addons` o `custom_addons` del servidor de Odoo.
2. Actualizar la lista de módulos desde **Aplicaciones** > **Actualizar
   lista**.
3. Instalar el módulo **"POS Mercado Pago QR (_mezztt)"**.

## Configuración del método de pago

1. Ingresar a **Punto de Venta > Configuración > Métodos de Pago**.
2. Crear (o editar) un método con tipo `qr_code` y seleccionar la interfaz
   de pago **"mercado_pago_qr_mezztt"**.
3. En el campo **Proveedor Mercado Pago** elegir el proveedor existente
   "Mercado Pago (Pago Online)" para reutilizar su Access Token y Public
   Key. Si el proveedor ya está correctamente configurado, el módulo tomará
   automáticamente esos valores.
4. Verificar que el proveedor de Mercado Pago tenga configurados los campos
   `Access Token` y `Public Key`.

## Credenciales fijas de la caja

El módulo utiliza un archivo Python dedicado para conservar las credenciales
específicas de cada caja/terminal. Editar el archivo
`pos_mercado_pago_mezztt/models/mp_config.py` y reemplazar los valores de
los siguientes campos:

```python
MP_ACCESS_TOKEN = "APP_USR-xxxxxxxxxxxxxxxxxxxx"
MP_PUBLIC_KEY = "APP_USR-xxxxxxxxxxxxxxxxxxxx"
COLLECTOR_ID = "123456789"
POS_ID = "POS001"
TERMINAL_ID = "TERMINAL001"
STORE_ID = "STORE001"
WEBHOOK_SECRET = ""
```

Estos valores son únicos para cada terminal y se obtienen desde el panel de
Mercado Pago (sección **Cajas**). El `WEBHOOK_SECRET` es opcional y permite
validar notificaciones entrantes.

## Flujo del POS

1. Seleccionar los productos y confirmar el pedido en el POS.
2. Elegir el método de pago **"Mercado Pago QR (_mezztt)"**.
3. El POS invocará al endpoint `/mp/mezztt/create`, generando un QR dinámico
   con el monto exacto. Se abrirá un popup mostrando la imagen QR.
4. El cliente escanea el QR y realiza el pago.
5. El POS consulta periódicamente el estado del pago mediante
   `/mp/mezztt/status` hasta que Mercado Pago lo apruebe.
6. Una vez aprobado, el popup mostrará el mensaje "Recibimos tu pago", se
   imprimirá el ticket y se retornará a la pantalla principal del POS.

## Webhooks

Mercado Pago puede enviar notificaciones al endpoint
`/mp/mezztt/webhook`. Configurar la URL pública correspondiente en el panel
de desarrollador de Mercado Pago y, opcionalmente, establecer el mismo
`WEBHOOK_SECRET` en ambos lados para validar la autenticidad de las
notificaciones.

## Solución de problemas

- **No se muestra el QR:** verificar que el método de pago tenga la
  interfaz `mercado_pago_qr_mezztt`, que el Access Token esté activo y que
  las credenciales del archivo `mp_config.py` sean correctas.
- **Errores de API:** habilitar los logs de depuración ejecutando Odoo con
  `--log-level=info` o `--log-level=debug` para revisar los mensajes
  `[MP][QR]` registrados con `_logger.info` y `_logger.error`.

## Compatibilidad

- Odoo 16 y 17.
- Punto de Venta estándar y modo tótem/autoservicio.
