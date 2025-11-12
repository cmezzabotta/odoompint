# POS Mercado Pago QR (_mezztt)

Extiende el Punto de Venta de Odoo 16/17 para cobrar con **Mercado Pago QR
dinámico**, utilizando la configuración del método de pago *Mercado Pago (Pago
Online)* y credenciales específicas por caja.

## 📦 Instalación

1. Copiar la carpeta `pos_mercado_pago_mezztt_base` dentro de `addons/` o
   `custom_addons/` de tu instalación de Odoo.
2. Actualizar la lista de módulos desde **Aplicaciones**.
3. Instalar *POS Mercado Pago QR (_mezztt)*.
4. Abrir `https://TU-ODOO/mp/mezztt/test` y verificar que devuelva el mensaje
   `Modulo POS Mercado Pago _mezztt operativo`.

## ⚙️ Configuración del método de pago

1. En **Facturación > Configuración > Proveedores de pago** (o **Pagos >
   Proveedores**), edita el proveedor *Mercado Pago (Pago Online)* y asegura que
   tenga definidos **Access Token** y **Public Key**. Estos valores serán leídos
   automáticamente por el módulo.
2. Navega a **Punto de Venta > Configuración > Métodos de pago** y localiza el
   método creado automáticamente **Mercado Pago QR (_mezztt)**.
3. Abre el registro y verifica:
   - Tipo: `qr_code`.
   - Interfaz de pago: `mercado_pago_qr_mezztt`.
   - Diario contable y cuenta de contrapartida según tus políticas contables.
4. Agrega el método al/los POS donde quieras ofrecer el pago.

> 💡 Si prefieres otros diarios o cuentas, edítalo luego de instalar el módulo.

## 🔐 Credenciales fijas por terminal

El Access Token y Public Key se obtienen del proveedor de pago. Las credenciales
de la caja (collector, POS, terminal) deben configurarse manualmente en:

```
pos_mercado_pago_mezztt_base/models/mp_config.py
```

Completa los siguientes valores con los datos provistos por Mercado Pago:

```python
MP_ACCESS_TOKEN = ""  # opcional, sólo si quieres forzarlo desde código
MP_PUBLIC_KEY = ""    # opcional
COLLECTOR_ID = "123456789"
POS_ID = "POS001"
EXTERNAL_POS_ID = "SUCURSAL1"
TERMINAL_ID = "CAJA01"
NOTIFICATION_URL = "https://tu-dominio.com/mp/mezztt/webhook"  # opcional
```

* `COLLECTOR_ID`, `POS_ID`, `EXTERNAL_POS_ID` y `TERMINAL_ID` son exclusivos de
  cada terminal/caja y se obtienen en el panel de desarrolladores de Mercado
  Pago (Instore > QR dinámico).
* Si `NOTIFICATION_URL` queda vacío, el módulo usará automáticamente la URL
  pública de Odoo + `/mp/mezztt/webhook`.

## 🧾 Flujo en el POS

1. El cajero selecciona los productos y elige **Mercado Pago QR (_mezztt)** como
   método de pago.
2. El POS genera un QR dinámico llamando a `/mp/mezztt/create_order` y abre un
   popup con el código y el monto exacto.
3. El cliente escanea el QR con la app de Mercado Pago y paga.
4. El POS consulta periódicamente `/mp/mezztt/payment_status` hasta obtener un
   estado `approved`.
5. Al aprobarse, se muestra el mensaje *“Recibimos tu pago”*, se imprime el
   ticket (si corresponde) y el POS vuelve al flujo normal.

## 🌐 Webhooks

El endpoint `/mp/mezztt/webhook` recibe notificaciones de Mercado Pago.

1. Configura la URL pública en el panel de desarrolladores de Mercado Pago (la
   misma que `NOTIFICATION_URL`).
2. Las notificaciones se registran en los logs de Odoo (`odoo.log`), útiles para
   auditoría o sincronización adicional.

## 🛠️ Solución de problemas

| Problema | Acción recomendada |
|----------|-------------------|
| El QR no se muestra | Revisa que `qr_image` esté llegando en la respuesta y que las credenciales de `mp_config.py` sean correctas. |
| Error “No se pudo generar el QR” | Activa los logs en modo debug (`--log-level=info`) y revisa la respuesta de Mercado Pago. |
| El pago nunca cambia a aprobado | Verifica el Access Token configurado en el proveedor y que el POS consulte `/mp/mezztt/payment_status`. |
| Webhook sin recibir | Comprueba la URL pública y accesible desde internet. |

## ✅ Compatibilidad

- Odoo 16 y 17.
- POS estándar, kiosco/tótem y modo autoservicio.
- No modifica archivos core de Odoo.

## 📚 Recursos adicionales

- Documentación oficial Mercado Pago QR: <https://www.mercadopago.com.ar/developers>
- Ajusta los textos y estilos del popup desde `static/src/xml/mp_qr_templates.xml`.

¡Listo! Tu POS ahora puede cobrar con Mercado Pago QR dinámico utilizando las
credenciales oficiales de tu cuenta.
