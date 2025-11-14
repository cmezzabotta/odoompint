/**
 * Popup OWL que conserva el diseño del prototipo original y orquesta el flujo
 * completo de pago: creación de la orden, polling y cierre exitoso.
 */

import { AbstractAwaitablePopup } from "@point_of_sale/app/utils/popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onWillUnmount, useState } from "@odoo/owl";

import { MP_CONFIG } from "./mp_config";

export class MercadoPagoPopup extends AbstractAwaitablePopup {
    static template = "mercado_pago_qr_mezztt.MercadoPagoPopup";

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            stage: "review", // review -> waiting -> success | error
            busy: false,
            status_message: "",
            order_id: null,
            pollHandle: null,
            pollStart: null,
        });
        onWillUnmount(() => this._stopPolling());
    }

    /** Finaliza el popup devolviendo el payload al PaymentTerminal. */
    _confirmSuccess(payload) {
        this._stopPolling();
        this.state.stage = "success";
        setTimeout(() => {
            this.confirm(payload);
        }, 5000);
    }

    _stopPolling() {
        if (this.state.pollHandle) {
            clearInterval(this.state.pollHandle);
            this.state.pollHandle = null;
        }
    }

    cancelPopup() {
        this._stopPolling();
        this.cancel();
    }

    async onPay() {
        if (this.state.busy || this.state.stage !== "review") {
            return;
        }
        this.state.busy = true;
        this.state.status_message = "";
        try {
            const payload = {
                pos_reference: this.props.pos_reference,
                total_amount: this.props.total,
                currency: this.props.currency,
                items: this.props.lines.map((line) => ({
                    name: line.display_name,
                    quantity: line.quantity,
                    unit_price: line.unit_price,
                    unit_measure: line.unit_measure,
                    external_code: line.external_code,
                })),
            };
            const response = await this.rpc("/mercado_pago_qr_mezztt/create_order", payload);
            if (response && response.order_id) {
                this.state.order_id = response.order_id;
                this.state.stage = "waiting";
                this.state.status_message = _t("Esperando confirmación de Mercado Pago…");
                this.props.onOrderCreated?.(response.order_id, response);
                this._startPolling();
            } else {
                const message = response && response.error ? response.error : _t("Orden no generada");
                this.state.stage = "error";
                this.state.status_message = message;
                this.notification.add(message, { type: "danger" });
            }
        } catch (err) {
            console.error("Mercado Pago order creation error", err);
            const message = err.message || String(err);
            this.state.stage = "error";
            this.state.status_message = message;
            this.notification.add(message, { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    _startPolling() {
        this._stopPolling();
        this.state.pollStart = Date.now();
        const interval = (MP_CONFIG.POLL_INTERVAL_SECONDS || 3) * 1000;
        this.state.pollHandle = setInterval(() => this._pollStatus(), interval);
    }

    async _pollStatus() {
        if (!this.state.order_id) {
            return;
        }
        const elapsed = (Date.now() - this.state.pollStart) / 1000;
        if (elapsed > (MP_CONFIG.POLL_TIMEOUT_SECONDS || 300)) {
            this._stopPolling();
            const message = _t("No se recibió confirmación de pago a tiempo.");
            this.state.stage = "error";
            this.state.status_message = message;
            this.notification.add(message, { type: "warning" });
            return;
        }
        try {
            const statusResponse = await this.rpc(
                `/mercado_pago_qr_mezztt/order_status/${this.state.order_id}`,
                {}
            );
            if (!statusResponse || statusResponse.error) {
                throw new Error(statusResponse?.error || "Respuesta inválida");
            }
            const status = statusResponse.status;
            if (status === "approved") {
                this._confirmSuccess({ orderId: this.state.order_id, status: statusResponse.raw });
            } else if (status === "rejected") {
                this._stopPolling();
                const message = _t("El pago fue rechazado por Mercado Pago.");
                this.state.stage = "error";
                this.state.status_message = message;
                this.notification.add(message, { type: "danger" });
                this.cancel({ reason: message });
            }
        } catch (err) {
            console.error("Mercado Pago polling error", err);
            const message = err.message || String(err);
            this.notification.add(message, { type: "warning" });
        }
    }
}

MercadoPagoPopup.defaultProps = {
    lines: [],
    total: 0,
    total_display: "",
    currency: "ARS",
    qr_url: MP_CONFIG.STATIC_QR_URL,
};
