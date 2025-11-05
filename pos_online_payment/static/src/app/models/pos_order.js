import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    setup() {
        super.setup();

        // Escuchar evento global de pago confirmado
        this.env.bus.addEventListener("confirm-paid", this._onMercadoPagoConfirmed);
    },

    _onMercadoPagoConfirmed(event) {
        const ref = event.detail.ref;
        const currentOrder = this.env.pos.get_order();

        if (!currentOrder) return;

        // Comparar referencia del pedido
        if (currentOrder.name === ref) {
            console.log(`[MP] Pago confirmado para orden: ${ref}`);
            this.env.pos.push_single_order(currentOrder);
        }
    },
});
