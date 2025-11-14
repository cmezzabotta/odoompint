# -*- coding: utf-8 -*-
"""Static Mercado Pago configuration used by both server and client code.

This module is deliberately **not** hooked to ``ir.config_parameter`` nor to any
backend configuration model.  The heladería must edit this file manually
whenever a new branch / POS device is onboarded.

Every value is documented in detail so that non-technical operators can locate
and update the credentials obtained from the official Mercado Pago backoffice.
"""

MP_CONFIG = {
    # ---------------------------------------------------------------------
    # ⚠️ IMPORTANTE: CAMBIAR ESTOS DATOS PARA CADA CAJA
    # ---------------------------------------------------------------------
    # ``STATIC_QR_URL``
    #   URL de la imagen del QR estático de la caja.  Mercado Pago entrega
    #   este enlace cuando se crea un código QR "Modo Estático" para el POS.
    #   Debe comenzar con ``https://`` y apuntar a una imagen PNG/JPG.
    "STATIC_QR_URL": "https://www.mercadopago.com/instore/merchant/qr/120858202/def9c0c87f7349d29b789703af8c8416b5a9120a9a004ca49d181eff79b19c1e.png",
    # ``COLLECTOR_ID``
    #   Identificador numérico de la cuenta de Mercado Pago que recibe los
    #   fondos.  Está disponible en la sección "Credenciales" del panel.
    "COLLECTOR_ID": "123456789",
    # ``POS_ID``
    #   Código externo del Punto de Venta (external_pos_id).  Debe coincidir
    #   exactamente con el configurado en Mercado Pago para la caja física.
    "POS_ID": "POS001",
    # ``BRANCH_ID``
    #   Identificador opcional de la sucursal (branch_id).  Solo completar si
    #   la cuenta de Mercado Pago lo exige; de lo contrario dejar ``None``.
    "BRANCH_ID": None,
    # ``ACCESS_TOKEN``
    #   Token privado (``access_token``) utilizado para firmar las llamadas a
    #   la API REST de Mercado Pago.  Se obtiene en "Credenciales" con el rol
    #   de producción o pruebas según el ambiente.
    "ACCESS_TOKEN": "APP_USR-XXXXXXXXXXXXXXXXXXX",
    # ``PUBLIC_KEY``
    #   Clave pública asociada al token anterior.  Solo se usa en frontend si
    #   se integran SDKs adicionales; la mantenemos documentada para futuras
    #   expansiones del POS.
    "PUBLIC_KEY": "APP_USR-XXXXXXXXXXXXXXXXXXX",
    # ``PLATFORM_ID`` y ``INTEGRATOR_ID``
    #   Datos opcionales para reportar integraciones oficiales.  Mercado Pago
    #   los entrega al socio tecnológico responsable del desarrollo.
    "PLATFORM_ID": None,
    "INTEGRATOR_ID": None,
    # ``SPONSOR_ID``
    #   Identificador del sponsor (partner comercial) en caso de corresponder.
    "SPONSOR_ID": None,
    # ``POLL_INTERVAL_SECONDS``
    #   Frecuencia con la que el POS consulta el estado de la orden.  Puede
    #   ajustarse entre 2 y 5 segundos según necesidad operativa.
    "POLL_INTERVAL_SECONDS": 3,
    # ``POLL_TIMEOUT_SECONDS``
    #   Tiempo máximo de espera antes de declarar que el pago quedó pendiente.
    #   Recomendado: 300 segundos (5 minutos).
    "POLL_TIMEOUT_SECONDS": 300,
}
