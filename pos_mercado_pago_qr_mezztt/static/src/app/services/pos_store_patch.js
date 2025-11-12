import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function collectPaymentMethods(posStore) {
    const buckets = [
        posStore.models?.["pos.payment.method"],
        posStore.payment_methods,
        posStore.paymentMethods,
        posStore.db?.payment_methods,
    ];

    const results = new Set();
    for (const bucket of buckets) {
        if (!bucket) {
            continue;
        }
        if (typeof bucket.getAll === "function") {
            for (const method of bucket.getAll()) {
                results.add(method);
            }
            continue;
        }
        if (typeof bucket.values === "function") {
            for (const method of bucket.values()) {
                results.add(method);
            }
            continue;
        }
        if (Array.isArray(bucket)) {
            for (const method of bucket) {
                results.add(method);
            }
            continue;
        }
        if (typeof bucket === "object") {
            for (const method of Object.values(bucket)) {
                results.add(method);
            }
        }
    }
    return [...results].filter(Boolean);
}

function methodUsesMercadoPago(method) {
    if (!method) {
        return false;
    }
    return (
        method.use_payment_terminal === "mercado_pago_qr" ||
        method.payment_terminal_id === "mercado_pago_qr" ||
        method.mpqr_use_qr === true ||
        method.mpqr_use_qr === 1
    );
}

function ensureTerminal(posStore, method, PaymentInterface) {
    if (!methodUsesMercadoPago(method) || !PaymentInterface) {
        return;
    }

    if (method.use_payment_terminal !== "mercado_pago_qr") {
        method.use_payment_terminal = "mercado_pago_qr";
    }

    const existing = method.payment_terminal;
    if (existing instanceof PaymentInterface) {
        return;
    }

    const terminal = new PaymentInterface(posStore, method);
    method.payment_terminal = terminal;
}

function assignMercadoPagoInterfaces(posStore) {
    const PaymentInterface = posStore.electronic_payment_interfaces?.mercado_pago_qr;
    if (!PaymentInterface) {
        return;
    }
    for (const method of collectPaymentMethods(posStore)) {
        ensureTerminal(posStore, method, PaymentInterface);
    }
}

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        assignMercadoPagoInterfaces(this);
    },

    async processServerData() {
        await super.processServerData(...arguments);
        assignMercadoPagoInterfaces(this);
    },

    async load_server_data() {
        await super.load_server_data(...arguments);
        assignMercadoPagoInterfaces(this);
    },
});
