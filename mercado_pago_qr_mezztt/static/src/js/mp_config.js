/**
 * Configuración estática de Mercado Pago disponible en el frontend del POS.
 *
 * ⚠️ IMPORTANTE: este archivo debe editarse cuando la heladería abra una nueva
 * caja o cambie de sucursal.  Los valores deben mantenerse sincronizados con
 * ``mp_config.py`` para que backend y frontend utilicen las mismas credenciales.
 */

export const MP_CONFIG = {
    /**
     * URL del QR estático asignado a la caja actual.
     * Mercado Pago entrega este enlace al crear un código QR "modo estático".
     * Para reemplazarlo copiar la URL completa (termina en .png) y pegarla aquí.
     */
    STATIC_QR_URL:
        "https://www.mercadopago.com/instore/merchant/qr/120858202/def9c0c87f7349d29b789703af8c8416b5a9120a9a004ca49d181eff79b19c1e.png",
    /**
     * Identificador numérico de la cuenta (collector_id) que cobrará la venta.
     * Se encuentra en la sección "Credenciales" del panel de Mercado Pago.
     */
    COLLECTOR_ID: "123456789",
    /**
     * Código externo del POS (external_pos_id).  Debe coincidir con el definido
     * en Mercado Pago para que la orden llegue a la caja correcta.
     */
    POS_ID: "POS001",
    /**
     * Identificador de sucursal.  Usar ``null`` si la cuenta no trabaja con
     * sucursales diferenciadas.
     */
    BRANCH_ID: null,
    /**
     * Token privado utilizado para crear órdenes vía API.  Solo el servidor lo
     * emplea, pero lo documentamos aquí para que sea sencillo ubicarlo.
     */
    ACCESS_TOKEN: "APP_USR-XXXXXXXXXXXXXXXXXXX",
    /**
     * Clave pública asociada al token anterior.  Se mantiene para futuras
     * integraciones que requieran exponerla en frontend.
     */
    PUBLIC_KEY: "APP_USR-XXXXXXXXXXXXXXXXXXX",
    /**
     * Identificadores opcionales otorgados por Mercado Pago a integradores
     * certificados.  Si la heladería no cuenta con ellos dejar ``null``.
     */
    PLATFORM_ID: null,
    INTEGRATOR_ID: null,
    SPONSOR_ID: null,
    /**
     * Intervalo de polling (en segundos) utilizado para consultar el estado de
     * la orden.  Valores típicos: 2 a 3 segundos.
     */
    POLL_INTERVAL_SECONDS: 3,
    /**
     * Tiempo máximo que se esperará antes de devolver control al cajero.
     */
    POLL_TIMEOUT_SECONDS: 300,
};
