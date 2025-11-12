/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { Gui } from "point_of_sale.Gui";
import { PaymentTerminal } from "point_of_sale.models";
import { AbstractAwaitablePopup } from "point_of_sale.AbstractAwaitablePopup";

class MercadoPagoMezzttPopup extends AbstractAwaitablePopup {}
MercadoPagoMezzttPopup.template = "MercadoPagoMezzttPopup";
MercadoPagoMezzttPopup.defaultProps = {
    title: _lt("Mercado Pago QR"),
    body: _lt("Escaneá el código QR desde la app de Mercado Pago."),
};

Gui.definePopup({ name: "MercadoPagoMezzttPopup", component: MercadoPagoMezzttPopup });

const MercadoPagoMezzttTerminal = {
    name: "mercado_pago_qr_mezztt",

    async send_payment_request(paymentLineId) {
        const paymentLine = this.pos.get_payment_line(paymentLineId);
        const order = this.pos.get_order();
        const paymentMethod = paymentLine.payment_method;
        const amount = paymentLine.amount;
        const partner = order.get_partner();
        const currency =
            order?.currency?.name ||
            order?.pricelist?.currency_id?.[1] ||
            paymentMethod?.currency_id?.[1] ||
            this.pos.currency?.name;
        const params = {
            payment_method_id: paymentMethod.id,
            amount: amount,
            currency: currency,
            pos_reference: order.name,
            description: order.export_for_printing().name,
            customer: partner
                ? {
                      name: partner.name,
                      email: partner.email,
                  }
                : null,
        };
        const response = await this._rpc({
            route: "/mp/mezztt/create",
            params,
        });
        paymentLine.terminalTransactionId = response.order_id;
        paymentLine.mpExternalReference = response.external_reference;
        Gui.showPopup("MercadoPagoMezzttPopup", {
            title: _lt("Mercado Pago QR"),
            amount: response.amount,
            currency: response.currency,
            qrImage: response.qr_image,
            qrData: response.qr_data,
        });
        return true;
    },

    async is_payment_approved(paymentLine) {
        if (!paymentLine.terminalTransactionId) {
            return true;
        }
        const result = await this._rpc({
            route: "/mp/mezztt/status",
            params: {
                payment_method_id: paymentLine.payment_method.id,
                order_id: paymentLine.terminalTransactionId,
            },
        });
        if (result.status === "approved") {
            Gui.showPopup("MercadoPagoMezzttPopup", {
                title: _lt("Recibimos tu pago"),
                body: _lt("Mercado Pago confirmó la acreditación."),
                amount: result.amount,
                currency: paymentLine.payment_method.currency_id[1],
            });
            return true;
        }
        if (result.status === "rejected") {
            throw new Error(_lt("El pago con Mercado Pago fue rechazado."));
        }
        return false;
    },

    async finalize_payment(paymentLine) {
        if (!paymentLine.terminalTransactionId) {
            return true;
        }
        const result = await this._rpc({
            route: "/mp/mezztt/status",
            params: {
                payment_method_id: paymentLine.payment_method.id,
                order_id: paymentLine.terminalTransactionId,
            },
        });
        if (result.status !== "approved") {
            throw new Error(_lt("El pago todavía no fue aprobado."));
        }
        Gui.closePopup();
        return true;
    },

    async cancel_payment(paymentLine) {
        if (!paymentLine.terminalTransactionId) {
            return true;
        }
        await this._rpc({
            route: "/mp/mezztt/cancel",
            params: {
                payment_method_id: paymentLine.payment_method.id,
                order_id: paymentLine.terminalTransactionId,
            },
        });
        Gui.closePopup();
        return true;
    },

    async _rpc(kwargs) {
        return await this.pos.env.services.rpc(kwargs);
    },
};

PaymentTerminal.register_terminal(MercadoPagoMezzttTerminal);
