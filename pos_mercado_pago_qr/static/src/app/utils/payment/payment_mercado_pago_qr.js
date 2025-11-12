import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import "@pos_mercado_pago_qr/app/services/pos_store_patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { MercadoPagoQrPopup } from "@pos_mercado_pago_qr/app/components/popups/mercado_pago_qr_popup/mercado_pago_qr_popup";

export class PaymentMercadoPagoQR extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.currentOrder = null;
        this.popupCloser = null;
    }

    // ---------------------------------------------------------------------
    // Legacy PaymentTerminal compatibility
    // ---------------------------------------------------------------------

    async send_payment_request(...args) {
        return this.sendPaymentRequest(...args);
    }

    async send_payment_cancel(...args) {
        return this.sendPaymentCancel(...args);
    }

    async send_payment_reversal(...args) {
        return this.sendPaymentReversal(...args);
    }

    async sendPaymentRequest() {
        await super.sendPaymentRequest(...arguments);
        const order = this.pos.getOrder();
        const paymentLine = order?.getSelectedPaymentline();
        if (!order || !paymentLine) {
            return false;
        }

        try {
            paymentLine.setPaymentStatus("waitingCard");
            const partner = order.getPartner();
            const orderData = {
                reference: order.name || order.uid,
                amount: Math.abs(paymentLine.amount),
                currency: this.pos.currency?.name,
                title: order.name || _t("POS Order"),
                description: (_t("Payment for %s") % (order.name || order.uid)),
                customer: partner
                    ? {
                          name: partner.name,
                          email: partner.email,
                      }
                    : {},
            };
            const payload = await this.env.services.orm.call(
                "pos.payment.method",
                "mpqr_prepare_order_payload",
                [[], orderData]
            );
            const orderInfo = await this.env.services.orm.call(
                "pos.payment.method",
                "mpqr_create_order",
                [[paymentLine.payment_method_id.id], payload]
            );

            this.currentOrder = {
                orderId: orderInfo.order_id,
                paymentMethodId: paymentLine.payment_method_id.id,
                externalReference: orderInfo.external_reference,
            };

            const formattedAmount = this.pos.env.utils.formatCurrency(orderInfo.amount || paymentLine.amount);
            const paymentResult = await new Promise((resolve) => {
                let resolved = false;
                const closeDialog = this.env.services.dialog.add(
                    MercadoPagoQrPopup,
                    {
                        orderName: payload.reference,
                        formattedAmount,
                        amount: orderInfo.amount,
                        currency: orderInfo.currency,
                        qrData: orderInfo.qr_data,
                        qrImage: orderInfo.qr_image,
                        expiresAt: orderInfo.expiration_date,
                        paymentMethodId: paymentLine.payment_method_id.id,
                        orderId: orderInfo.order_id,
                        onApprove: () => {
                            resolved = true;
                            resolve(true);
                        },
                        onReject: (message) => {
                            if (message) {
                                this._showMessage(message, "info");
                            }
                            resolved = true;
                            resolve(false);
                        },
                    },
                    {
                        onClose: () => {
                            if (!resolved) {
                                this._cancelCurrentOrder();
                                resolve(false);
                            }
                        },
                    }
                );
                this.popupCloser = () => {
                    closeDialog();
                    if (!resolved) {
                        this._cancelCurrentOrder();
                        resolve(false);
                    }
                };
            });

            if (!paymentResult) {
                paymentLine.setPaymentStatus("retry");
                this.currentOrder = null;
                return false;
            }

            paymentLine.setPaymentStatus("done");
            this.currentOrder = null;
            return true;
        } catch (error) {
            console.error("[MercadoPagoQR]", error);
            this._showMessage(error.message || error, "error");
            paymentLine.setPaymentStatus("retry");
            return false;
        } finally {
            this.popupCloser = null;
        }
    }

    async sendPaymentCancel(order, cid) {
        await super.sendPaymentCancel(order, cid);
        await this._cancelCurrentOrder();
        return true;
    }

    async sendPaymentReversal(order, cid) {
        return await this.sendPaymentCancel(order, cid);
    }

    async _cancelCurrentOrder() {
        if (!this.currentOrder) {
            return;
        }
        try {
            await this.env.services.orm.silent.call(
                "pos.payment.method",
                "mpqr_cancel_order",
                [[this.currentOrder.paymentMethodId], this.currentOrder.orderId]
            );
        } catch (error) {
            console.warn("[MercadoPagoQR] Unable to cancel order", error);
        }
        this.currentOrder = null;
    }

    _showMessage(message, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: (_t("Mercado Pago %s") % title),
            body: message,
        });
    }
}

register_payment_method("mercado_pago_qr", PaymentMercadoPagoQR);
