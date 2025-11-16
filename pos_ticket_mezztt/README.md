# POS Ticket Mezztt

Este módulo extiende el TPV de Odoo 18 Community para la emisión automática de ticket fiscal válido ante AFIP desde kioskos de autoservicio.

## Características

- Generación automática de facturas electrónicas tipo B/C durante la validación del pedido POS.
- Solicitud del CAE y datos asociados a través de `l10n_ar_afipws` sin intervención humana.
- Construcción del QR fiscal AFIP como imagen base64 lista para impresoras térmicas de 80 mm.
- Impresión automática del ticket fiscal con número de orden, fecha, detalle de productos, CAE, vencimiento, CUIT, punto de venta, condición de IVA del cliente y QR scanneable.
- Manejo de errores controlado: el ticket no se imprime si AFIP no responde y se muestra un mensaje claro para reintentos.

## Requisitos previos

1. **Configuración fiscal** completa de Argentina (`l10n_ar` + `l10n_ar_afipws`).
2. Diario de facturación asignado al TPV y POS configurado para facturación automática.
3. Cliente por defecto con CUIT/Condición IVA válida (por ej. Consumidor Final).
4. Librería Python `qrcode` instalada en el servidor Odoo:
   ```bash
   pip install qrcode[pil]
   ```

## Flujo de operación

1. El cliente paga la orden en el tótem (Mercado Pago, etc.).
2. Al validar la orden, el módulo crea/postea la factura y solicita el CAE a AFIP.
3. Se generan los datos fiscales + QR y se guardan en `pos.order`.
4. El frontend del POS consulta esos datos antes de imprimir y auto-lanza la impresión.
5. Si AFIP no responde o falta algún dato (CAE/QR), se muestra un error y el operador puede reintentar desde el backend.

## Reprocesar órdenes con error

1. Revisar el pedido en **Punto de Venta → Pedidos**.
2. Validar desde el backend que exista factura asociada.
3. Usar el botón *Reenviar a AFIP* / volver a `action_post` según corresponda.
4. Una vez obtenido el CAE, el POS recuperará los datos y permitirá imprimir.

## Mantenimiento

- El template QWeb `static/src/xml/fiscal_ticket_template.xml` controla el layout del ticket; puede ajustarse para otras impresoras manteniendo el ancho de 80 mm en el CSS.
- La lógica fiscal reside en `models/pos_order.py`. Allí puede personalizarse el manejo de errores, diarios o condiciones especiales.
- Los assets JS/CSS se encuentran declarados en el manifest para cargarse únicamente en el POS.
- Ante cambios en AFIP, verificar si hay nuevos campos en `l10n_ar_afipws` y mapearlos en `_fill_fiscal_data_from_invoice`.

## Soporte

Documentar cualquier incidencia en el pedido POS (campo **Mensaje de error fiscal**) para que el personal técnico pueda monitorear conexiones AFIP desde el backend.
