/**
 * PaymentTerminal que coordina el popup Mercado Pago QR con el flujo interno
 * del Punto de Venta.
 */

import { registry } from "@web/core/registry";
import { PaymentTerminal } from "@point_of_sale/app/payment/terminal/payment_terminal";
import { _t } from "@web/core/l10n/translation";

import { MercadoPagoPopup } from "./mercado_pago_popup";
import { MP_CONFIG } from "./mp_config";

const paymentTerminalRegistry = registry.category("pos_payment_terminal");

export class MercadoPagoQrMezzttTerminal extends PaymentTerminal {
    constructor(env, config) {
        super(env, config);
        this.popup = this.env.services.popup;
        this.notification = this.env.services.notification;
        this.pos = this.env.services.pos;
    }

    /**
     * Entrada principal utilizada por el POS cuando se presiona el botón de pago.
     */
    async send_payment_request(arg1, arg2) {
        const paymentLine = arg2 || arg1;
        if (!paymentLine) {
            throw new Error("Línea de pago inválida");
        }
        const order = this.pos.get_order();
        if (!order) {
            throw new Error("No hay pedido activo");
        }
        // Señalizamos al POS que el terminal está atendiendo la solicitud.
        paymentLine.set_payment_status("waiting");
        const format = (amount) => this.pos.formatCurrency(amount);
        const lines = order.get_orderlines().map((line) => {
            const product = line.product;
            // Se envían datos enriquecidos para mostrarlos en el popup y para
            // construir la carga útil hacia Mercado Pago (título, unidad, etc.).
            return {
                id: line.id || line.cid,
                display_name: product.display_name || product.name,
                quantity: line.get_quantity(),
                quantity_display: line.get_quantity_str ? line.get_quantity_str() : line.get_quantity(),
                unit_price: line.get_unit_price(),
                unit_price_display: format(line.get_unit_price()),
                total_price_display: format(line.get_price_with_tax()),
                unit_measure: product.uom_id?.[1] || "unit",
                external_code: product.default_code || product.id,
            };
        });
        const total = order.get_total_with_tax();
        const popupProps = {
            title: _t("Mercado Pago QR"),
            pos_reference: order.uid,
            total,
            total_display: format(total),
            currency: order.currency?.name || this.pos.currency.name,
            lines,
            qr_url: MP_CONFIG.STATIC_QR_URL,
            onOrderCreated: (orderId) => {
                // Guardamos el identificador de la orden por si el cajero
                // necesita consultarlo desde el backend.
                paymentLine.set_payment_status("waiting");
                paymentLine.mp_order_id = orderId;
            },
        };
        const { confirmed, payload } = await this.popup.add(MercadoPagoPopup, popupProps);
        if (confirmed) {
            paymentLine.set_payment_status("done");
            paymentLine.transaction_id = payload?.orderId;
            // Validamos la orden actual y creamos un nuevo pedido vacío para
            // preparar el siguiente cobro automáticamente.
            await this.pos.validateOrder();
            this.pos.add_new_order();
            return true;
        }
        // El cajero puede volver a intentar si el cliente necesita repetir.
        paymentLine.set_payment_status("retry");
        return false;
    }

    /** El POS consulta este método para saber si el terminal soporta reintentos. */
    is_payment_terminal_compatible() {
        return true;
    }
}

paymentTerminalRegistry.add("mercado_pago_qr_mezztt", MercadoPagoQrMezzttTerminal);
