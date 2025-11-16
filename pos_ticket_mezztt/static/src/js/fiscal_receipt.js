/** @odoo-module **/

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { Order } from "@point_of_sale/app/store/order";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

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

const superPrintReceipt = ReceiptScreen.prototype.printReceipt;
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
    },
    async printReceipt() {
        try {
            await this._ensureFiscalTicketData();
        } catch (error) {
            this.notification.add(
                error?.message || _t("No se pudo emitir el ticket fiscal. Reintente nuevamente."),
                { type: "danger" }
            );
            throw error;
        }
        return superPrintReceipt.apply(this, arguments);
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
            throw new Error(_t("No se recibieron datos fiscales desde el servidor."));
        }
        if (payload.fiscal_error_message) {
            throw new Error(payload.fiscal_error_message);
        }
        if (!payload.cae) {
            throw new Error(_t("La AFIP todavía no entregó un CAE para esta orden. Reintente la impresión."));
        }
        order.setFiscalTicketData(payload);
    },
    shouldAutoPrint() {
        return true;
    },
});
