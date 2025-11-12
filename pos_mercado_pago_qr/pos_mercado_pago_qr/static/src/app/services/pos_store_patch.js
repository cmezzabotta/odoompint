import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function attachTerminal(posStore, paymentMethod) {
    if (paymentMethod.use_payment_terminal !== "mercado_pago_qr") {
        return;
    }
    const PaymentInterface = posStore.electronic_payment_interfaces?.mercado_pago_qr;
    if (!PaymentInterface) {
        return;
    }
    if (!(paymentMethod.payment_terminal instanceof PaymentInterface)) {
        paymentMethod.payment_terminal = new PaymentInterface(posStore, paymentMethod);
    }
}

function assignMercadoPagoQrInterface(posStore) {
    const paymentMethods = posStore.models?.["pos.payment.method"];
    if (!paymentMethods) {
        return;
    }
    for (const method of paymentMethods.getAll()) {
        attachTerminal(posStore, method);
    }
}

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        assignMercadoPagoQrInterface(this);
    },

    async processServerData() {
        await super.processServerData(...arguments);
        assignMercadoPagoQrInterface(this);
    },
});
