/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { PaymentTerminal } from "point_of_sale.models";
import { MpQrPopup } from "../popups/mp_qr_popup";

const MercadoPagoQRMezztt = {
    name: "mercado_pago_qr_mezztt",

    _reset() {
        this._context = null;
    },

    async send_payment_request(paymentMethod, paymentLine) {
        const pos = paymentLine.pos;
        this.pos = pos;
        const order = pos.get_order();
        const rpc = pos.env.services.rpc;
        const notification = pos.env.services.notification;
        const popup = pos.env.services.popup;

        try {
            const response = await rpc(
                "/mp/mezztt/create_order",
                {
                    amount: Math.abs(paymentLine.amount),
                    currency: pos.currency?.name || "ARS",
                    order_reference: order?.uid || order?.name,
                    description: order?.name,
                    payment_method_id: paymentMethod?.id || paymentLine.payment_method?.id,
                }
            );

            this._context = {
                external_reference: response.external_reference,
                payment_method_id: paymentMethod?.id || paymentLine.payment_method?.id,
                payment_id: response.payment_id,
            };

            await popup.add(MpQrPopup, {
                title: _t("Mercado Pago QR"),
                body: _t("Esperando confirmación de pago desde Mercado Pago."),
                qrImage: response.qr_image,
                qrData: response.qr_data,
                amount: Math.abs(paymentLine.amount),
                currency: pos.currency?.symbol || pos.currency?.name || "ARS",
                terminal_id: response.terminal_id,
                external_reference: response.external_reference,
            });

            notification.add(_t("QR generado. Esperando aprobación de Mercado Pago."), {
                type: "info",
            });
            return true;
        } catch (error) {
            console.error("Mercado Pago QR error", error);
            notification.add(_t("No se pudo generar el QR de Mercado Pago."), {
                type: "danger",
            });
            this._reset();
            throw error;
        }
    },

    async is_payment_approved() {
        if (!this.pos || !this._context) {
            return false;
        }
        const rpc = this.pos.env.services.rpc;
        try {
            const status = await rpc("/mp/mezztt/payment_status", {
                external_reference: this._context.external_reference,
                payment_method_id: this._context.payment_method_id,
                payment_id: this._context.payment_id,
            });
            if (status.payment_id) {
                this._context.payment_id = status.payment_id;
            }
            if (status.status === "approved") {
                this.pos.env.services.notification.add(
                    _t("Recibimos tu pago de Mercado Pago."),
                    { type: "success" }
                );
                return true;
            }
            return false;
        } catch (error) {
            console.error("Mercado Pago QR status error", error);
            return false;
        }
    },

    async finalize_payment() {
        const approved = await this.is_payment_approved();
        if (!approved) {
            throw new Error("mercado_pago_qr_mezztt_not_approved");
        }
        this._reset();
        return true;
    },

    async cancel() {
        this._reset();
        return true;
    },
};

PaymentTerminal.register_terminal(MercadoPagoQRMezztt);
