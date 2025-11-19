import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import "@mezztt_qr_api_complete/app/services/pos_store_patch";
import { MpQrPopup } from "@mezztt_qr_api_complete/app/components/mp_qr_popup/mp_qr_popup";

export class PaymentMpQrStatic extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.currentOrder = null;
        this.popupCloser = null;
    }

    async sendPaymentRequest() {
        await super.sendPaymentRequest(...arguments);
        const order = this.pos.getOrder();
        const paymentLine = order?.getSelectedPaymentline();
        if (!order || !paymentLine) {
            return false;
        }
        const method = paymentLine.payment_method_id;
        if (!method?.mp_qr_enabled) {
            return false;
        }
        const partner = order.getPartner();
        const orderPayload = {
            reference: order.name || order.uid,
            title: order.name || _t("Orden POS"),
            description: (_t("Pago de %s") % (order.name || order.uid)),
            amount: Math.abs(paymentLine.amount),
            currency: this.pos.currency?.name,
            customer_name: partner?.name,
            customer_email: partner?.email,
        };
        try {
            paymentLine.setPaymentStatus("waitingCard");
            const orderInfo = await this.env.services.orm.call(
                "pos.payment.method",
                "mpqr_static_create_order",
                [[method.id], orderPayload]
            );
            if (!orderInfo?.id) {
                throw new Error(_t("Mercado Pago no devolvió un identificador de orden."));
            }
            const formattedAmount = this.pos.env.utils.formatCurrency(Math.abs(paymentLine.amount));
            const paymentResult = await new Promise((resolve) => {
                let resolved = false;
                const closeDialog = this.env.services.dialog.add(
                    MpQrPopup,
                    {
                        orderName: orderPayload.reference,
                        formattedAmount,
                        qrUrl: method.mp_qr_static,
                        paymentMethodId: method.id,
                        orderId: orderInfo.id,
                        onApprove: () => {
                            resolved = true;
                            resolve(true);
                        },
                        onReject: () => {
                            resolved = true;
                            resolve(false);
                        },
                    },
                    {
                        onClose: () => {
                            if (!resolved) {
                                resolve(false);
                            }
                        },
                    }
                );
                this.popupCloser = () => {
                    closeDialog();
                    if (!resolved) {
                        resolve(false);
                    }
                };
            });
            this.popupCloser = null;
            if (!paymentResult) {
                paymentLine.setPaymentStatus("retry");
                return false;
            }
            paymentLine.setPaymentStatus("done");
            await this._showThankYou();
            return true;
        } catch (error) {
            console.error("[MP-QR-STATIC]", error);
            this.env.services.notification.add(error.message || error, { type: "danger" });
            paymentLine.setPaymentStatus("retry");
            return false;
        }
    }

    async sendPaymentCancel(order, cid) {
        await super.sendPaymentCancel(order, cid);
        if (this.popupCloser) {
            this.popupCloser();
            this.popupCloser = null;
        }
        return true;
    }

    async sendPaymentReversal(order, cid) {
        return this.sendPaymentCancel(order, cid);
    }

    async _showThankYou() {
        await new Promise((resolve) => {
            const closeDialog = this.env.services.dialog.add(AlertDialog, {
                title: _t("Gracias por tu compra"),
                body: _t("El pago fue aprobado por Mercado Pago."),
            });
            setTimeout(() => {
                closeDialog();
                resolve();
            }, 2500);
        });
    }
}

register_payment_method("mercado_pago_qr_static", PaymentMpQrStatic);
