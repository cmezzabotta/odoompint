import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function assignMercadoPagoQrInterface(posStore) {
    const PaymentInterface = posStore.electronic_payment_interfaces?.mercado_pago_qr;
    if (!PaymentInterface) {
        return;
    }
    const paymentMethods = posStore.models?.["pos.payment.method"];
    if (!paymentMethods) {
        return;
    }
    for (const method of paymentMethods.getAll()) {
        if (method.use_payment_terminal === "mercado_pago_qr" && !method.payment_terminal) {
            method.payment_terminal = new PaymentInterface(posStore, method);
        }
    }
}

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        assignMercadoPagoQrInterface(this);
    },
});
