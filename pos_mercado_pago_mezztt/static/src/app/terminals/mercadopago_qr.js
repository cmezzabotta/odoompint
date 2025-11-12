/** @odoo-module **/

import { PaymentTerminal } from "point_of_sale.models";
import { Gui } from "point_of_sale.Gui";
import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";

const POPUP_NAME = "MpQrPopup";
const JSON_HEADERS = { "Content-Type": "application/json" };

async function jsonRequest(url, { method = "POST", body } = {}) {
    const response = await fetch(url, {
        method,
        headers: JSON_HEADERS,
        body: body ? JSON.stringify(body) : undefined,
        credentials: "include",
    });
    if (!response.ok) {
        throw new Error(sprintf(_t("No pudimos comunicarnos con el servidor (%s)."), response.status));
    }
    const payload = await response.json();
    if (payload && payload.error) {
        throw new Error(payload.error);
    }
    return payload;
}

const MercadoPagoQRMezztt = {
    name: "mercado_pago_qr_mezztt",
    async send_payment_request(_paymentLine) {
        this.lastPaymentResult = null;
        const pos = this.env.pos;
        const order = pos.get_order();
        const amount = order ? order.get_due() : 0;
        if (!order || amount <= 0) {
            throw new Error(_t("La orden no tiene saldo pendiente."));
        }

        const payload = {
            amount,
            currency: pos.currency?.name,
            order_ref: order.uid,
            pos_session_id: pos.pos_session?.id,
        };

        const createResponse = await jsonRequest("/mp/mezztt/create", { body: payload });
        const popupResult = await Gui.showPopup(POPUP_NAME, {
            title: _t("Mercado Pago QR"),
            amount,
            currency: payload.currency,
            qr_base64: createResponse.qr_base64,
            qr_url: createResponse.qr_url,
            payment_id: createResponse.payment_id,
        });

        if (!popupResult.confirmed) {
            throw new Error(popupResult?.payload?.message || _t("El pago fue cancelado."));
        }

        this.lastPaymentResult = {
            status: "approved",
            paymentId: createResponse.payment_id,
            metadata: popupResult.payload?.metadata || {},
        };
        return true;
    },
    async is_payment_approved() {
        return Boolean(this.lastPaymentResult && this.lastPaymentResult.status === "approved");
    },
    async finalize_payment() {
        return true;
    },
    async cancel_payment() {
        this.lastPaymentResult = null;
        return true;
    },
};

PaymentTerminal.register_terminal(MercadoPagoQRMezztt);
