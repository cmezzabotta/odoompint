/** @odoo-module **/

import { PaymentTerminal } from "point_of_sale.models";

const MercadoPagoQR = {
    name: "mercado_pago_qr",

    init(pos, paymentMethod) {
        this.pos = pos;
        this.paymentMethod = paymentMethod;
    },

    _findPaymentLine(paymentLineCid) {
        const order = this.pos?.get_order();
        if (!order) {
            return null;
        }
        if (!paymentLineCid) {
            return order.selected_paymentline || order.get_selected_paymentline?.();
        }
        const paymentLines = order.paymentlines?.models || order.get_paymentlines?.();
        if (!paymentLines) {
            return null;
        }
        for (const line of paymentLines) {
            if (line?.cid === paymentLineCid) {
                return line;
            }
        }
        return null;
    },

    _dispatchToInterface(methodName, paymentLineCid, ...args) {
        const order = this.pos?.get_order();
        const paymentLine = this._findPaymentLine(paymentLineCid);
        if (paymentLine && typeof order?.select_paymentline === "function") {
            order.select_paymentline(paymentLine);
        }
        const terminal = paymentLine?.payment_method?.payment_terminal;
        const handler = terminal && (terminal[methodName] || terminal[methodName.replace(/_/g, "")]);
        if (typeof handler !== "function") {
            console.warn("[MercadoPagoQR][legacy] Missing handler", methodName);
            return Promise.resolve(false);
        }
        try {
            return handler.call(terminal, order, paymentLineCid, ...args);
        } catch (error) {
            console.error("[MercadoPagoQR][legacy] Handler error", error);
            return Promise.resolve(false);
        }
    },

    send_payment_request(paymentLineCid, ...args) {
        return this._dispatchToInterface("sendPaymentRequest", paymentLineCid, ...args);
    },

    send_payment_cancel(paymentLineCid, ...args) {
        return this._dispatchToInterface("sendPaymentCancel", paymentLineCid, ...args);
    },

    send_payment_reversal(paymentLineCid, ...args) {
        return this._dispatchToInterface("sendPaymentReversal", paymentLineCid, ...args);
    },
};

PaymentTerminal.register_terminal(MercadoPagoQR);
