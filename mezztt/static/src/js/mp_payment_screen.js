odoo.define('mezztt.MPPaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const MercadoPagoPaymentScreen = (PaymentScreen) => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            const currentOrder = this.env.pos.get_order();
            if (currentOrder && currentOrder.mercadoPagoApproved) {
                currentOrder.mercadoPagoApproved = false;
                return super.validateOrder(...arguments);
            }
            const selectedPaymentline = currentOrder && currentOrder.selected_paymentline;
            if (selectedPaymentline && selectedPaymentline.payment_method && selectedPaymentline.payment_method.id === this.env.pos.config.mezztt_payment_method_id) {
                const locale = (this.env.pos.lang || 'es_AR').replace('_', '-');
                const formatter = new Intl.NumberFormat(locale, {
                    style: 'currency',
                    currency: this.env.pos.currency.name,
                });
                const items = currentOrder.get_orderlines().map((line) => ({
                    id: line.product.id,
                    name: line.get_full_product_name(),
                    qty: line.get_quantity(),
                    price: line.get_unit_price(),
                    total: line.get_price_with_tax(),
                    price_formatted: formatter.format(line.get_unit_price()),
                    total_formatted: formatter.format(line.get_price_with_tax()),
                }));
                const payload = {
                    total: currentOrder.get_total_with_tax(),
                    currency: this.env.pos.currency.name,
                    order_uid: currentOrder.uid,
                    items: items,
                };
                await this.showPopup('MercadoPagoQrPopup', {
                    items: items,
                    total: currentOrder.get_total_with_tax(),
                    total_formatted: formatter.format(currentOrder.get_total_with_tax()),
                    backendPayload: {
                        order_uid: currentOrder.uid,
                        amount: currentOrder.get_total_with_tax(),
                        currency: this.env.pos.currency.name,
                        items: items.map((it) => ({
                            id: it.id,
                            name: it.name,
                            quantity: it.qty,
                            unit_price: it.price,
                            total: it.total,
                        })),
                    },
                    onPaymentCreated: (data) => {
                        currentOrder.set_mezztt_payment_reference(data.external_reference);
                        this._schedulePaymentStatusCheck(currentOrder, data);
                    },
                    currency: this.env.pos.currency.name,
                    onPaid: () => {
                        currentOrder.mercadoPagoApproved = true;
                        this.validateOrder(true);
                    },
                });
                return false;
            }
            return super.validateOrder(...arguments);
        }

        _schedulePaymentStatusCheck(order, data) {
            if (!order || !data || !data.external_reference) {
                return;
            }
            order.mezzttPaymentInfo = {
                external_reference: data.external_reference,
                expires_at: Date.now() + 300000,
            };
        }
    };

    Registries.Component.extend(PaymentScreen, MercadoPagoPaymentScreen);

    return MercadoPagoPaymentScreen;
});
