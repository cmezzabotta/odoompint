import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function attachTerminal(posStore, paymentMethod, PaymentInterface) {
    if (!paymentMethod || paymentMethod.use_payment_terminal !== "mercado_pago_qr") {
        return;
    }
    if (!PaymentInterface) {
        return;
    }

    const existingTerminal = paymentMethod.payment_terminal;
    if (existingTerminal instanceof PaymentInterface) {
        // Ensure the legacy API is available on the modern interface instance.
        ensureLegacyAliases(existingTerminal);
        return;
    }

    const terminal = new PaymentInterface(posStore, paymentMethod);
    ensureLegacyAliases(terminal);
    paymentMethod.payment_terminal = terminal;
}

function ensureLegacyAliases(terminal) {
    if (typeof terminal.send_payment_request !== "function" && typeof terminal.sendPaymentRequest === "function") {
        terminal.send_payment_request = (...args) => terminal.sendPaymentRequest(...args);
    }
    if (typeof terminal.send_payment_cancel !== "function" && typeof terminal.sendPaymentCancel === "function") {
        terminal.send_payment_cancel = (...args) => terminal.sendPaymentCancel(...args);
    }
    if (typeof terminal.send_payment_reversal !== "function" && typeof terminal.sendPaymentReversal === "function") {
        terminal.send_payment_reversal = (...args) => terminal.sendPaymentReversal(...args);
    }
}

function gatherPaymentMethods(posStore) {
    const methods = new Set();

    const model = posStore.models?.["pos.payment.method"];
    if (model) {
        if (typeof model.getAll === "function") {
            for (const record of model.getAll()) {
                methods.add(record);
            }
        } else if (Array.isArray(model.records)) {
            for (const record of model.records) {
                methods.add(record);
            }
        }
    }

    const collection = posStore.payment_methods || posStore.paymentMethods;
    if (collection) {
        if (typeof collection.values === "function") {
            for (const record of collection.values()) {
                methods.add(record);
            }
        } else if (Array.isArray(collection)) {
            for (const record of collection) {
                methods.add(record);
            }
        }
    }

    return [...methods];
}

function assignMercadoPagoQrInterface(posStore) {
    const PaymentInterface = posStore.electronic_payment_interfaces?.mercado_pago_qr;
    if (!PaymentInterface) {
        return;
    }
    for (const method of gatherPaymentMethods(posStore)) {
        attachTerminal(posStore, method, PaymentInterface);
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
