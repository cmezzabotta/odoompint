/** @odoo-module **/
import { PaymentTerminal } from "point_of_sale.models";

const MercadoPagoQRMezztt = {
    name: "mercado_pago_qr_mezztt",
    async send_payment_request() {
        console.log("🟢 Simulando envío de pago a Mercado Pago...");
        return true;
    },
};

PaymentTerminal.register_terminal(MercadoPagoQRMezztt);
