import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class OnlinePaymentPopup extends Component {
    static template = "pos_online_payment.OnlinePaymentPopup";
    static components = { Dialog };
    static props = {
        qrCode: String,
        formattedAmount: String,
        orderName: String,
        orderTotal: order.get_total_with_tax(),
        close: Function,
    };

    setup() {
        super.setup();
    }

    mounted() {
        super.mounted();
        const ref = this.props.orderName;
        const amount = this.props.orderTotal;

        // Paso 1: Crear orden en Mercado Pago
        fetch("/pos/create_mercadopago_order", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                reference: ref,
                amount: amount,
            }),
        })
        .then((res) => res.json())
        .then((data) => {
            if (data.error) {
                console.error("Error al crear orden MP:", data.error);
                this.showError("No se pudo iniciar el pago con Mercado Pago.");
            } else {
                // Orden creada correctamente, iniciar polling
                this.startPolling(ref);
            }
        })
        .catch((err) => {
            console.error("Error HTTP:", err);
            this.showError("Error de comunicación con el backend.");
        });
    }

    async startPolling(ref) {
        const poll = async () => {
            try {
                const res = await fetch(`/pos/mercado_pago_status/${ref}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                const data = await res.json();
                if (data.paid) {
                    this.close();  // cerrar el popup
                    this.env.services.bus.trigger("confirm-paid", { ref });  // lanzar evento global
                } else {
                    setTimeout(poll, 3000);  // reintenta luego de 3 seg
                }
            } catch (err) {
                console.error("Polling error", err);
                setTimeout(poll, 5000);  // intenta de nuevo luego de error
            }
        };
        poll();
    }

    showError(message) {
        alert(message);
    }
}
