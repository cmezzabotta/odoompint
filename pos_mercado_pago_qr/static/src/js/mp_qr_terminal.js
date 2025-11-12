/** @odoo-module **/

import { PaymentTerminal } from "point_of_sale.models";

const MercadoPagoQR = {
    name: "mercado_pago_qr",

    async send_payment_request(payment_line_uuid) {
        console.log('🟢 Enviando solicitud de pago para:', payment_line_uuid);
        return true; // Simula éxito
    },

    async is_payment_approved(payment_line) {
        return true;
    },

    async finalize_payment(payment_line) {
        return true;
    },

    async cancel_payment(payment_line) {
        return true;
    }
};

PaymentTerminal.register_terminal(MercadoPagoQR);
