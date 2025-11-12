/** @odoo-module **/
import { PaymentTerminal } from "point_of_sale.models";
import { registry } from "@web/core/registry";
import { Gui } from "point_of_sale.Gui";
import { _t } from "@web/core/l10n/translation";
import { MpQrPopup } from "../popups/mp_qr_popup";

const Rpc = (route, params={}) => fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params),credentials:'include'}).then(r=>r.json());

const MercadoPagoQRMezztt = {
    name: "mercado_pago_qr_mezztt",
    async send_payment_request(payment_line_uuid){
        const pos = this.env.pos;
        const order = pos.get_order();
        const amount = order.get_due();
        const order_ref = order.uid;
        const createRes = await Rpc("/mp/mezztt/create",{amount,currency:pos.currency.name,order_ref});
        if(createRes.error) throw new Error(createRes.error);
        const { confirmed } = await Gui.showPopup(MpQrPopup.name,{title:_t("Mercado Pago QR"),qr_base64:createRes.qr_base64,qr_url:createRes.qr_url,payment_id:createRes.payment_id});
        return confirmed;
    },
    async is_payment_approved(){ return true; },
    async finalize_payment(){ return true; },
    async cancel_payment(){ return true; }
};
PaymentTerminal.register_terminal(MercadoPagoQRMezztt);
registry.category("popups").add(MpQrPopup.name, MpQrPopup);
