/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { Order } from "@point_of_sale/app/store/order";

// --- PATCH: Datos fiscales del pedido ---
const superExportForPrinting = Order.prototype.export_for_printing;
patch(Order.prototype, {
    setFiscalTicketData(fiscalData) {
        this.fiscalTicketData = fiscalData || {};
        this.fiscalTicketDataLoaded = true;
    },
    hasFiscalTicketData() {
        return Boolean(this.fiscalTicketDataLoaded);
    },
    getFiscalTicketData() {
        return this.fiscalTicketData || {};
    },
    export_for_printing() {
        const result = superExportForPrinting.apply(this, arguments);
        return Object.assign(result, this.getFiscalTicketData());
    },
});

// --- PATCH: Pantalla de recibo ---
const superSetup = ReceiptScreen.prototype.setup;
patch(ReceiptScreen.prototype, {
    setup() {
        superSetup.call(this);
        this.rpc = useService("rpc");
        this.notification = useService("notification");

        onMounted(async () => {
            const order = this.currentOrder;
            if (order && order.is_to_invoice()) {
                try {
                    await this._ensureFiscalTicketData();
                } catch (error) {
                    this.notification.add(
                        error?.message || _t("No se pudo emitir el ticket fiscal."),
                        { type: "danger" }
                    );
                }
            }
        });
    },

    async _ensureFiscalTicketData() {
        const order = this.currentOrder;
        if (!order || order.hasFiscalTicketData() || !order.backendId) {
            return;
        }

        const payload = await this.rpc("/pos/order/receipt_fiscal", {
            order_id: order.backendId,
        });

        if (!payload) {
            throw new Error(_t("No se recibieron datos fiscales del servidor."));
        }

        if (payload.fiscal_error_message) {
            throw new Error(payload.fiscal_error_message);
        }

        if (!payload.cae) {
            throw new Error(_t("La AFIP aún no entregó el CAE. Reintente."));
        }

        order.setFiscalTicketData(payload);
    },

    shouldAutoPrint() {
        return true;
    },
});

// Usar plantilla conmutada que decide si imprime el ticket fiscal propio
// o el recibo estándar según el modo de facturación del pedido.
ReceiptScreen.template = "pos_ticket_mezztt.FiscalAwareOrderReceipt";
