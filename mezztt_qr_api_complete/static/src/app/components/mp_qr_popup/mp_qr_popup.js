import { Component, onWillUnmount, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const POLLING_DELAY = 3000;

export class MpQrPopup extends Component {
    static template = "mezztt_qr_api_complete.MpQrPopup";
    static components = { Dialog };
    static props = {
        orderName: { type: String },
        formattedAmount: { type: String },
        qrUrl: { type: String },
        paymentMethodId: { type: Number },
        orderId: { type: Number },
        onApprove: { type: Function },
        onReject: { type: Function },
        close: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ status: "pending", message: _t("Esperando confirmación...") });
        this._stop = false;
        this._pollHandle = null;
        onWillUnmount(() => this._stopPolling());
    }

    mounted() {
        this._startPolling();
    }

    async _startPolling() {
        if (this._stop) {
            return;
        }
        try {
            const result = await this.orm.silent.call(
                "pos.payment.method",
                "mpqr_static_poll",
                [[this.props.paymentMethodId], this.props.orderId]
            );
            if (result.status === "approved") {
                this.state.status = "approved";
                this.state.message = _t("Pago aprobado por Mercado Pago.");
                this.props.onApprove?.(result);
                this.props.close();
                return;
            }
            if (["rejected", "cancelled", "expired"].includes(result.status)) {
                this.state.status = result.status;
                const labelMap = {
                    rejected: _t("rechazado"),
                    cancelled: _t("cancelado"),
                    expired: _t("vencido"),
                };
                const label = labelMap[result.status] || result.status;
                this.state.message = _t("El pago fue %s").replace("%s", label);
                this.props.onReject?.(result);
                this.props.close();
                return;
            }
        } catch (error) {
            console.error("[MP-QR-STATIC][poll]", error);
            this.state.status = "error";
            this.state.message = error.message || error;
            this.notification.add(error.message || error, { type: "danger" });
            this.props.onReject?.(error);
            this.props.close();
            return;
        }
        this._pollHandle = setTimeout(() => this._startPolling(), POLLING_DELAY);
    }

    _stopPolling() {
        this._stop = true;
        if (this._pollHandle) {
            clearTimeout(this._pollHandle);
            this._pollHandle = null;
        }
    }

    cancelPayment() {
        this._stopPolling();
        this.state.status = "cancelled";
        this.state.message = _t("El pago fue cancelado desde el POS.");
        this.props.onReject?.({ status: "cancelled" });
        this.props.close();
    }
}
