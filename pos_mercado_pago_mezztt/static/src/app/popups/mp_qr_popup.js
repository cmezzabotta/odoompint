/** @odoo-module **/

import { useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { AbstractAwaitablePopup } from "point_of_sale.ConfirmPopup";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

const STATUS_MESSAGES = {
    pending: _t("Esperando pago..."),
    approved: _t("Recibimos tu pago"),
    rejected: _t("Pago rechazado"),
    cancelled: _t("Pago cancelado"),
    error: _t("No pudimos obtener el estado del pago"),
};

export class MpQrPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        this.state = useState({
            status: "pending",
            seconds: 0,
            message: STATUS_MESSAGES.pending,
            metadata: null,
        });
        this._timer = null;
        this._poller = null;
        this._retryTimer = null;
        onWillStart(() => this._startTimers());
        onWillUnmount(() => this._clearTimers());
    }

    async _pollStatus() {
        if (!this.props.payment_id) {
            return;
        }
        try {
            const response = await fetch(`/mp/mezztt/status/${encodeURIComponent(this.props.payment_id)}`, {
                method: "GET",
                credentials: "include",
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const payload = await response.json();
            if (payload.error) {
                throw new Error(payload.error);
            }
            const status = payload.status || "pending";
            this.state.status = status;
            this.state.message = STATUS_MESSAGES[status] || STATUS_MESSAGES.pending;
            this.state.metadata = payload.metadata || null;
            if (status === "approved" || status === "rejected" || status === "cancelled") {
                this._clearTimers();
                if (status === "approved") {
                    this.confirm({ metadata: this.state.metadata });
                } else {
                    this.cancel({
                        status,
                        message: this.state.message,
                        metadata: this.state.metadata,
                    });
                }
            }
        } catch (error) {
            this.state.status = "error";
            this.state.message = `${STATUS_MESSAGES.error} (${error.message})`;
            if (!this._retryTimer) {
                this._retryTimer = setTimeout(() => {
                    this.state.status = "pending";
                    this.state.message = STATUS_MESSAGES.pending;
                    this._retryTimer = null;
                }, 4000);
            }
        }
    }

    _startTimers() {
        this._timer = setInterval(() => {
            this.state.seconds += 1;
            if (this.state.seconds >= 120 && this.state.status === "pending") {
                this.cancel({
                    status: "cancelled",
                    message: _t("Se alcanzó el tiempo máximo de espera."),
                    metadata: this.state.metadata,
                });
            }
        }, 1000);
        this._poller = setInterval(() => {
            if (this.state.status === "pending") {
                this._pollStatus();
            }
        }, 2500);
    }

    _clearTimers() {
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
        if (this._poller) {
            clearInterval(this._poller);
            this._poller = null;
        }
        if (this._retryTimer) {
            clearTimeout(this._retryTimer);
            this._retryTimer = null;
        }
    }

    cancel(payload) {
        const status = payload?.status || "cancelled";
        this.state.status = status;
        this.state.message = payload?.message || STATUS_MESSAGES[status] || STATUS_MESSAGES.cancelled;
        super.cancel(payload || { message: this.state.message, status });
    }
}

MpQrPopup.name = "MpQrPopup";
MpQrPopup.template = "pos_mercado_pago_mezztt.MpQrPopup";
MpQrPopup.defaultProps = {
    title: _t("Mercado Pago QR"),
    body: "",
};

registry.category("popups").add(MpQrPopup.name, MpQrPopup);
