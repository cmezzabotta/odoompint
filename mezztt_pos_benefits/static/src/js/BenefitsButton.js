/** @odoo-module **/

import { PosComponent } from "@point_of_sale/app/components/pos_component";
import { useListener } from "@web/core/utils/hooks";
import { BenefitsPopup } from "./BenefitsPopup";

export class BenefitsButton extends PosComponent {
    setup() {
        useListener("click", this.openPopup);
    }

    async openPopup() {
        this.env.services.popup.add(BenefitsPopup, {});
    }
}

BenefitsButton.template = "BenefitsButton";

export const PosBenefitsButton = {
    component: BenefitsButton,
};

odoo.define("mezztt_pos_benefits.Button", function(require){
    const { ProductScreen } = require("@point_of_sale/app/screens/product_screen/product_screen");
    ProductScreen.addControlButton({
        component: BenefitsButton,
        condition: () => true,
    });
});
