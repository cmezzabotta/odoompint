/** @odoo-module **/

import { PaymentTerminal } from "point_of_sale.models";

const MercadoPagoQR = {
    name: "mercado_pago_qr",
};

PaymentTerminal.register_terminal(MercadoPagoQR);
