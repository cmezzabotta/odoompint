/** @odoo-module **/

import publicWidget from "web.public.widget";
import ajax from "web.ajax";

publicWidget.registry.MercadoPagoQR = publicWidget.Widget.extend({
    selector: ".o_mercado_pago_qr_instructions",
    start() {
        this.reference = this.el.dataset.reference;
        if (this.reference) {
            this._startPolling();
        }
        return this._super(...arguments);
    },
    destroy() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
        }
        return this._super(...arguments);
    },
    async _startPolling() {
        const statusEl = this.el.querySelector(".o_mp_qr_status");
        const updateStatus = (text) => {
            if (statusEl) {
                statusEl.textContent = text || "";
            }
        };
        updateStatus(this.el.dataset.initialMessage);
        this._pollInterval = setInterval(async () => {
            try {
                const result = await ajax.jsonRpc(`/payment/mercado_pago_qr/status/${this.reference}`, "call", {});
                if (!result || result.state === "not_found") {
                    updateStatus("Transacción no encontrada.");
                    return;
                }
                if (result.error) {
                    updateStatus(result.error);
                    return;
                }
                if (result.mercado_pago_status) {
                    updateStatus(`Estado en Mercado Pago: ${result.mercado_pago_status}`);
                }
                if (result.state === "done") {
                    updateStatus("Pago acreditado. Redirigiendo...");
                    clearInterval(this._pollInterval);
                    window.location.reload();
                } else if (result.state === "cancel" || result.state === "error") {
                    updateStatus("El pago fue cancelado en Mercado Pago.");
                    clearInterval(this._pollInterval);
                }
            } catch (error) {
                updateStatus("No se pudo actualizar el estado del pago.");
                console.error("Mercado Pago QR polling error", error);
            }
        }, 5000);
    },
});
