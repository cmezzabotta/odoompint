/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { AbstractAwaitablePopup } from "point_of_sale.ConfirmPopup";

export class MpQrPopup extends AbstractAwaitablePopup {}

MpQrPopup.template = "pos_mercado_pago_mezztt.MpQrPopup";
MpQrPopup.defaultProps = {
    title: _t("Escanea el código QR"),
    confirmText: _t("Cerrar"),
    body: "",
    qrImage: null,
    qrData: null,
    amount: 0,
    currency: "",
};

registry.category("pos_popups").add("MpQrPopup", MpQrPopup);
