/** @odoo-module **/

import { PaymentTerminal } from "point_of_sale.models";

const MercadoPagoQR = {
    name: "mercado_pago_qr",

    async send_payment_request(request) {
        const paymentLineUuid = typeof request === "string" ? request : request?.paymentLineUuid;
        const order = this.env.pos.get_order();
        const payment_line = paymentLineUuid
            ? order.paymentlines.find((pl) => pl.uuid === paymentLineUuid)
            : order.getSelectedPaymentline?.();
        if (!payment_line) {
            throw new Error("No se encontró la línea de pago.");
        }

        const order_id = order.backendId;
        const resp = await fetch("/mp/qr/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id }),
        });
        const data = await resp.json();

        if (data.error) {
            throw new Error(data.error);
        }

        const link = data.link;
        console.log("🟢 Link de Mercado Pago:", link);

        const win = window.open(link, "_blank");
        if (!win) {
            alert("Permite ventanas emergentes para abrir el link de Mercado Pago.");
        }

        return true;
    },

    async is_payment_approved(payment_line) {
        return true;
    },

    async finalize_payment(payment_line) {
        return true;
    },

    async cancel_payment(payment_line) {
        return true;
    },
};

PaymentTerminal.register_terminal(MercadoPagoQR);
