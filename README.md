# Guía de instalación: Integración Mercado Pago QR para POS de Odoo

Esta guía describe cómo desplegar el módulo **`pos_mp_complete_setup`**, que añade al Punto de Venta de Odoo el flujo de cobro con código QR estático de Mercado Pago y la validación automática del pedido cuando se confirma el pago.

## 1. Requisitos previos

1. **Odoo** 16.0 o superior (edición Community o Enterprise) con el módulo **Punto de Venta** instalado.
2. Acceso al servidor donde se ejecuta Odoo (por SSH o de forma local) con permisos para administrar el servicio.
3. Credenciales de Mercado Pago con QR estático activo para la caja que recibirá los cobros.
4. Dependencias del sistema en el servidor Odoo:
   - Python 3.10+
   - Node.js 18+ (para reconstruir activos web si corresponde)
   - `git` y utilidades básicas de shell.
5. Control sobre el archivo de configuración de Odoo (`odoo.conf`) para añadir rutas personalizadas de addons.

## 2. Descargar el código del módulo

1. Conéctate al servidor y sitúate en el directorio donde guardas los addons personalizados, por ejemplo:
   ```bash
   cd /opt/odoo/custom/addons
   ```
2. Clona este repositorio (o copia el contenido proporcionado) en el directorio de addons:
   ```bash
   git clone https://tu-servidor.git/pos_mp_complete_setup.git
   ```
   > Si recibiste el paquete como archivo `.zip`, descomprímelo en el mismo directorio y conserva la estructura `pos_mp_complete_setup/pos_online_payment/...`.

## 3. Registrar el módulo en Odoo

1. Abre el archivo de configuración `odoo.conf` y asegúrate de que la ruta del repositorio se encuentre en la clave `addons_path`, por ejemplo:
   ```ini
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom/addons
   ```
2. Guarda los cambios y reinicia el servicio de Odoo (comando orientativo, ajusta según tu despliegue):
   ```bash
   sudo systemctl restart odoo
   ```

## 4. Actualizar la lista de aplicaciones e instalar

1. Inicia sesión en el backend de Odoo con un usuario administrador.
2. Activa el **modo desarrollador** desde Ajustes → Activar modo desarrollador.
3. Navega a **Aplicaciones** y pulsa **Actualizar la lista de aplicaciones**.
4. Busca el módulo **POS Mercado Pago QR** (el nombre mostrado corresponde al contenido de `pos_mp_complete_setup`).
5. Pulsa **Instalar**. Al finalizar, el POS ya cargará los activos JavaScript incluidos en este repositorio.

## 5. Configuración de Mercado Pago

1. En Mercado Pago, verifica que la caja tenga un **QR estático** configurado y toma nota del identificador.
2. En el backend de Odoo, accede a la configuración específica del POS/Mercado Pago (menú creado por tu personalización) y registra:
   - El identificador del punto de venta/caja.
   - Token de acceso de la aplicación Mercado Pago.
   - La URL base para crear órdenes (si cuentas con un microservicio intermedio).
3. Asegúrate de que las rutas HTTP utilizadas por el frontend existan en tu servidor de Odoo o middleware:
   - `POST /pos/create_mercadopago_order` debe generar la preferencia de pago y devolver el identificador de referencia.
   - `POST /pos/mercado_pago_status/<referencia>` debe consultar Mercado Pago y devolver `{ "paid": true }` cuando el cobro se confirme.

## 6. Verificación del flujo en el POS

1. Abre el Punto de Venta en el navegador.
2. Crea una orden de prueba y elige la opción de pago con QR.
3. Al pulsar **Validar**, se abrirá el popup que muestra el QR, el monto y las instrucciones. El código JavaScript crea la orden en Mercado Pago y comienza un sondeo periódico.
4. Escanea el QR con la app de Mercado Pago y realiza el pago. Al confirmarse, el popup se cierra automáticamente y el pedido pasa a la pantalla de checkout sin intervención manual.
5. Comprueba en el backend que la orden se registró correctamente como pagada.

## 7. Solución de problemas

- **El popup no muestra el QR o la cantidad**: revisa en las herramientas de desarrollador del navegador que los activos del módulo se carguen; si no, limpia la caché de Odoo (`/web?debug=assets`) y vuelve a construir los assets.
- **La orden no se valida automáticamente**: confirma que el endpoint `POST /pos/mercado_pago_status/<referencia>` devuelva `{"paid": true}` cuando Mercado Pago reporta el pago.
- **Errores al crear la orden**: consulta los logs del servidor de Odoo; el módulo registra la llamada `/pos/create_mercadopago_order` y la respuesta. Verifica credenciales y conectividad con Mercado Pago.
- **Necesidad de recompilar assets**: si usas Odoo en modo producción con assets minificados, ejecuta:
  ```bash
  ./odoo-bin -c /etc/odoo/odoo.conf --upgrade pos_mp_complete_setup --stop-after-init
  ```
  para reconstruir los bundles de JavaScript y asegurar que los cambios queden disponibles.

## 8. Actualizaciones futuras

1. Para aplicar nuevas versiones de este repositorio, sitúate dentro de `pos_mp_complete_setup` y ejecuta:
   ```bash
   git pull origin main
   ```
2. Reinicia el servicio de Odoo y repite el proceso de actualización de lista de aplicaciones si fuese necesario.

Con estos pasos deberías tener el flujo de cobro con Mercado Pago QR operativo en tu Punto de Venta de Odoo.
