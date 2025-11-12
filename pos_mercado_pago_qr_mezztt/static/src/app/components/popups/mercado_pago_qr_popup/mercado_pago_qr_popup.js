import { Component, onWillUnmount, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { qrCodeSrc } from "@point_of_sale/utils";
import { _t } from "@web/core/l10n/translation";

const POLLING_DELAY = 4000;

export class MercadoPagoQrPopup extends Component {
    static template = "pos_mercado_pago_qr_mezztt.MercadoPagoQrPopup";
    static components = { Dialog };
    static props = {
        orderName: { type: String },
        formattedAmount: { type: String },
        amount: { type: Number, optional: true },
        currency: { type: String, optional: true },
        qrData: { type: String, optional: true },
        qrImage: { type: String, optional: true },
        expiresAt: { type: String, optional: true },
        paymentMethodId: { type: Number },
        orderId: { type: Number },
        onApprove: { type: Function, optional: true },
        onReject: { type: Function, optional: true },
        close: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            status: "pending",
            qrImage: this.props.qrImage || (this.props.qrData ? qrCodeSrc(this.props.qrData) : null),
            errorMessage: null,
        });
        this._pollHandle = null;
        this._stopped = false;
        onWillUnmount(() => this._stopPolling());
    }

    mounted() {
        this._startPolling();
    }

    async _startPolling() {
        if (this._stopped) {
            return;
        }
        try {
            const result = await this.orm.silent.call(
                "pos.payment.method",
                "mpqr_poll_order",
                [[this.props.paymentMethodId], this.props.orderId]
            );
            const status = result.status;
            if (status === "approved") {
                this.state.status = "approved";
                this.props.onApprove?.(result);
                this.props.close();
                return;
            }
            if (["rejected", "cancelled", "expired", "error"].includes(status)) {
                this.state.status = status;
                const message = this._statusMessage(status, result);
                this.state.errorMessage = message;
                this.props.onReject?.(message);
                this.props.close();
                return;
            }
        } catch (error) {
            console.error("[MercadoPagoQR][poll]", error);
            const message = error.message || error;
            this.state.status = "error";
            this.state.errorMessage = message;
            this.props.onReject?.(message);
            this.props.close();
            return;
        }
        this._pollHandle = setTimeout(() => this._startPolling(), POLLING_DELAY);
    }

    _stopPolling() {
        this._stopped = true;
        if (this._pollHandle) {
            clearTimeout(this._pollHandle);
            this._pollHandle = null;
        }
    }

    async cancelPayment() {
        this._stopPolling();
        try {
            await this.orm.silent.call(
                "pos.payment.method",
                "mpqr_cancel_order",
                [[this.props.paymentMethodId], this.props.orderId]
            );
        } catch (error) {
            console.warn("[MercadoPagoQR] cancel", error);
            this.notification.add(_t("The cancellation request could not be sent to Mercado Pago."), {
                type: "warning",
            });
        }
        const message = _t("The QR payment was cancelled from the POS.");
        this.state.status = "cancelled";
        this.props.onReject?.(message);
        this.props.close();
    }

    _statusMessage(status, result) {
        switch (status) {
            case "approved":
                return _t("Payment approved by Mercado Pago.");
            case "rejected":
                return _t("The customer rejected the payment in Mercado Pago.");
            case "cancelled":
                return _t("The QR payment was cancelled in Mercado Pago.");
            case "expired":
                return _t("The QR code expired before the payment was confirmed.");
            case "error":
            default:
                return result?.detail || _t("Mercado Pago did not confirm the payment.");
        }
    }
}
