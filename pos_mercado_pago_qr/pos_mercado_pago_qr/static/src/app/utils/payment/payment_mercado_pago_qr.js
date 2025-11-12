/** @odoo-module **/

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

    async send_payment_request(paymentRequest = {}) {
        return this.sendPaymentRequest(paymentRequest);
    }

    async sendPaymentRequest(paymentRequest = {}) {
        await super.sendPaymentRequest(paymentRequest);
        const order = this.pos.getOrder();
        if (!order) {
            return false;
        }

        const paymentLineUuid = paymentRequest.paymentLineUuid;
        let paymentLine = null;
        if (paymentLineUuid) {
            paymentLine = order.paymentlines?.find((pl) => pl.uuid === paymentLineUuid) || null;
        }
        paymentLine = paymentLine || order.getSelectedPaymentline?.();
        if (!paymentLine) {
            return false;
        }

        try {
            paymentLine.setPaymentStatus("waitingCard");
            const partner = order.getPartner?.();
            const amount = Math.abs(paymentLine.amount);
            const paymentMethod = paymentLine.payment_method_id;
            const reference = paymentRequest.reference || order.name || order.uid;
            const description =
                paymentRequest.description || (_t("Payment for %s") % (reference || order.uid));
            const currency = paymentRequest.currency || this.pos.currency?.name;
            const baseMetadata = {
                order_uid: order.uid,
                session_id: this.pos.pos_session?.id,
            };
            const orderData = {
                reference,
                amount,
                currency,
                title: paymentRequest.title || order.name || _t("POS Order"),
                description,
                customer:
                    paymentRequest.customer ||
                    (partner
                        ? {
                              name: partner.name,
                              email: partner.email,
                          }
                        : {}),
                items: this._buildItems(paymentRequest.items, order),
                metadata: {
                    ...baseMetadata,
                    ...(paymentRequest.metadata || {}),
                },
                integrator_id: paymentRequest.integrator_id || paymentMethod.mpqr_integrator_id,
                external_pos_id: paymentRequest.external_pos_id || paymentMethod.mpqr_pos_external_id,
                store_id: paymentRequest.store_id || paymentMethod.mpqr_store_id,
                expiration_minutes:
                    paymentRequest.expiration_minutes || paymentMethod.mpqr_order_validity,
                total_amount: paymentRequest.total_amount || amount,
                payment_amount: paymentRequest.payment_amount || amount,
                qr_mode: paymentRequest.qr_mode || 'static',
            };
            const payload = await this.env.services.orm.call(
                "pos.payment.method",
                "mpqr_prepare_order_payload",
                [[], orderData]
            );
            const orderInfo = await this.env.services.orm.call(
                "pos.payment.method",
                "mpqr_create_order",
                [[paymentMethod.id], payload]
            );

            this.currentOrder = {
                orderId: orderInfo.order_id,
                paymentMethodId: paymentMethod.id,
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
                        paymentMethodId: paymentMethod.id,
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

    _buildItems(requestItems, order) {
        if (Array.isArray(requestItems) && requestItems.length) {
            return requestItems;
        }
        const items = [];
        const orderlines = order?.get_orderlines?.() || [];
        for (const line of orderlines) {
            const printable = typeof line.export_for_printing === "function" ? line.export_for_printing() : {};
            const product = line.get_product?.() || line.product || {};
            const title =
                printable.product_name || product.display_name || product.name || _t("POS Item");
            const unitPriceRaw =
                printable.price_unit ??
                printable.price ??
                (typeof line.get_unit_price === "function" ? line.get_unit_price() : null) ??
                0;
            const quantityRaw =
                printable.quantity ??
                printable.qty ??
                (typeof line.get_quantity === "function" ? line.get_quantity() : null) ??
                1;
            const unitMeasure =
                printable.unit_measure ||
                printable.uom ||
                (Array.isArray(product.uom_id) ? product.uom_id[1] : product.uom_id) ||
                "unit";
            const externalCode = product.default_code || product.barcode || product.id || null;
            const categories = [];
            const categoryId = Array.isArray(product.pos_categ_id)
                ? product.pos_categ_id[0]
                : product.pos_categ_id;
            if (categoryId) {
                categories.push({ id: String(categoryId) });
            }
            const unitPrice = Math.abs(parseFloat(unitPriceRaw) || 0);
            const quantity = Math.abs(parseFloat(quantityRaw) || 0);
            items.push({
                title,
                description: printable.full_product_name || printable.product_name || title,
                unit_price: unitPrice,
                quantity: quantity || 1,
                unit_measure: unitMeasure,
                external_code: externalCode,
                external_categories: categories,
            });
        }
        return items;
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
