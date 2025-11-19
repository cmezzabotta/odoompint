/** @odoo-module **/

import { PosComponent } from "@point_of_sale/app/components/pos_component";
import { useState } from "@odoo/owl";
import { ErrorPopup } from "@point_of_sale/app/components/popups/error_popup";

export class BenefitsPopup extends PosComponent {
    setup() {
        this.state = useState({
            tab: "giftcard",
            giftcard: "",
            coupon: "",
        });
    }

    switchTab(tab) {
        this.state.tab = tab;
    }

    async applyGiftcard() {
        if (!this.state.giftcard) {
            return this.showError("Ingresá un código.");
        }

        const result = await this.rpc({
            model: "pos.giftcard",
            method: "search_read",
            domain: [["name", "=", this.state.giftcard], ["active", "=", true]],
            fields: ["balance"],
        });

        if (!result.length) {
            return this.showError("Giftcard inválida.");
        }

        const balance = result[0].balance;

        const order = this.env.pos.get_order();
        const due = order.get_due();

        const to_apply = Math.min(balance, due);

        order.add_paymentline(order.payment_methods[0]);
        const line = order.selected_paymentline;
        line.set_amount(-to_apply);

        await this.rpc({
            model: "pos.giftcard",
            method: "consume_amount",
            args: [result[0].id, to_apply],
        });

        this.cancel();
    }

    async applyCoupon() {
        if (!this.state.coupon)
            return this.showError("Ingresá un cupón.");

        const result = await this.rpc({
            model: "pos.coupon",
            method: "search_read",
            domain: [["code", "=", this.state.coupon], ["active", "=", true]],
            fields: ["type", "value"],
        });

        if (!result.length)
            return this.showError("Cupón inválido.");

        const coupon = result[0];
        const order = this.env.pos.get_order();
        const due = order.get_due();

        let to_apply = 0;

        if (coupon.type === "fixed") {
            to_apply = Math.min(coupon.value, due);
        } else {
            to_apply = (order.get_total_with_tax() * coupon.value) / 100;
        }

        order.add_paymentline(order.payment_methods[0]);
        const line = order.selected_paymentline;
        line.set_amount(-to_apply);

        this.cancel();
    }

    showError(msg) {
        this.env.services.popup.add(ErrorPopup, { title: "Error", body: msg });
    }

    cancel() {
        this.trigger("close-popup");
    }
}

BenefitsPopup.template = "BenefitsPopup";
