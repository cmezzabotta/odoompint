odoo.define('pos_mp_qr_base.MpQrIntegration', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const models = require('point_of_sale.models');
    const { useState, useRef, onMounted, onWillUnmount } = owl;

    async function jsonRpc(route, params) {
        const response = await fetch(route, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Date.now() }),
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        let payload;
        try {
            payload = await response.json();
        } catch (err) {
            throw new Error('Respuesta inválida del servidor');
        }
        if (payload.error) {
            const error = payload.error;
            const message = (error.data && error.data.message) || error.message || error;
            throw new Error(message);
        }
        return payload.result || {};
    }

    class MpQrPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            this.state = useState({
                qrData: null,
                qrUrl: null,
                status: 'idle',
                error: null,
                status_detail: null,
                loading: false,
                externalReference: null,
                transactionId: null,
                timeout: null,
                elapsed: 0,
            });
            this.qrContainer = useRef('qrContainer');
            onMounted(() => {
                if (this.props.autoStart) {
                    this.generateQr();
                }
            });
            onWillUnmount(() => this._clearPolling());
        }

        get order() {
            return this.props.order;
        }

        get remainingSeconds() {
            if (!this.state.timeout) {
                return null;
            }
            const remaining = Math.max(this.state.timeout - this.state.elapsed, 0);
            return remaining > 0 ? remaining : 0;
        }

        async generateQr() {
            if (this.state.loading) {
                return;
            }
            this.state.loading = true;
            this.state.error = null;
            this.state.status_detail = null;
            this.state.status = 'request';
            try {
                const response = await jsonRpc('/mercadopago/qr', {
                    amount: this.props.amount,
                    description: this.props.description || this.order.get_name(),
                    external_reference: this.props.external_reference,
                    currency: this.props.currency,
                    order_uid: this.order.uid,
                    pos_session_id: this.env.pos.pos_session && this.env.pos.pos_session.id,
                });
                this.state.externalReference = response.external_reference;
                this.state.transactionId = response.transaction_id;
                this.state.qrData = response.qr_base64 ? `data:image/png;base64,${response.qr_base64}` : null;
                this.state.qrUrl = response.init_point;
                this.state.timeout = response.timeout_seconds;
                this.state.status = 'waiting';
                this.state.elapsed = 0;
                setTimeout(() => this._renderQr(), 0);
                this._startPolling();
            } catch (error) {
                this.state.error = error.message || this.env._t('Error inesperado generando el QR');
                this.state.status = 'error';
            } finally {
                this.state.loading = false;
            }
        }

        _startPolling() {
            this._clearPolling();
            this._polling = setInterval(() => {
                this._pollStatus();
            }, 3000);
        }

        _clearPolling() {
            if (this._polling) {
                clearInterval(this._polling);
                this._polling = null;
            }
        }

        async _pollStatus() {
            try {
                this.state.elapsed += 3;
                if (this.state.timeout && this.state.elapsed >= this.state.timeout) {
                    this.state.error = this.env._t('Se agotó el tiempo de espera del pago.');
                    this._clearPolling();
                    this.cancel({ reason: 'timeout', error: this.state.error });
                    return;
                }
                const result = await jsonRpc('/mercadopago/status', {
                    external_reference: this.state.externalReference,
                });
                this.state.status_detail = result.status_detail || null;
                if (result.status === 'approved') {
                    this._clearPolling();
                    this.state.status = 'approved';
                    this.confirm({
                        status: 'approved',
                        payment_id: result.payment_id,
                        amount: result.amount || this.props.amount,
                        external_reference: this.state.externalReference,
                        transaction_id: this.state.transactionId,
                    });
                } else if (result.status === 'cancelled' || result.status === 'rejected') {
                    this._clearPolling();
                    this.state.error = this.env._t('El pago fue cancelado o rechazado por Mercado Pago.');
                    this.state.status = 'error';
                    this.cancel({ reason: 'cancelled', error: this.state.error });
                    return;
                }
            } catch (error) {
                this._clearPolling();
                this.state.error = error.message || this.env._t('Error consultando el estado del pago.');
                this.state.status = 'error';
                this.cancel({ reason: 'error', error: this.state.error });
                return;
            }
        }

        _renderQr() {
            if (this.state.qrData || !this.state.qrUrl || !this.qrContainer.el) {
                return;
            }
            if (window.QRCode) {
                this.qrContainer.el.innerHTML = '';
                // eslint-disable-next-line no-new
                new window.QRCode(this.qrContainer.el, {
                    text: this.state.qrUrl,
                    width: 256,
                    height: 256,
                    correctLevel: window.QRCode.CorrectLevel.H,
                });
            }
        }

        cancel(payload) {
            this._clearPolling();
            super.cancel(payload);
        }

        onCancel() {
            this.cancel({ reason: 'user_cancelled' });
        }
    }

    MpQrPopup.template = 'MpQrPopup';
    Registries.Component.add(MpQrPopup);

    const PaymentScreenMp = (PaymentScreenBase) => class extends PaymentScreenBase {
        async addNewPaymentLine(paymentMethod, options) {
            if (paymentMethod.mp_use_qr) {
                const order = this.currentOrder;
                if (!order) {
                    return super.addNewPaymentLine(paymentMethod, options);
                }
                const amountDue = order.get_due();
                if (amountDue <= 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Mercado Pago QR'),
                        body: this.env._t('No hay monto pendiente para cobrar.'),
                    });
                    return;
                }
                const { confirmed, payload } = await this.showPopup('MpQrPopup', {
                    title: this.env._t('Mercado Pago QR'),
                    order,
                    paymentMethod,
                    amount: amountDue,
                    description: order.get_name(),
                    external_reference: order.uid,
                    currency: this.env.pos.currency && this.env.pos.currency.name,
                    autoStart: true,
                });
                if (confirmed && payload && payload.status === 'approved') {
                    const paymentLine = order.add_paymentline(paymentMethod);
                    if (paymentLine) {
                        paymentLine.set_amount(payload.amount || amountDue);
                        paymentLine.setMpPaymentData({
                            payment_id: payload.payment_id,
                            external_reference: payload.external_reference,
                            transaction_id: payload.transaction_id,
                        });
                    }
                    try {
                        await this.validateOrder(false);
                    } catch (error) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Mercado Pago QR'),
                            body: error.message || this.env._t('No se pudo validar la orden.'),
                        });
                    }
                } else if (payload && payload.error) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Mercado Pago QR'),
                        body: payload.error,
                    });
                } else if (!confirmed && payload && payload.reason === 'timeout') {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Mercado Pago QR'),
                        body: this.env._t('El pago no se confirmó a tiempo. Intentalo nuevamente.'),
                    });
                } else if (!confirmed && payload && payload.reason === 'cancelled') {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Mercado Pago QR'),
                        body: this.env._t('Mercado Pago rechazó el intento de pago.'),
                    });
                }
                return;
            }
            return super.addNewPaymentLine(paymentMethod, options);
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenMp);

    const ReceiptScreenMp = (ReceiptScreenBase) => class extends ReceiptScreenBase {
        setup() {
            super.setup();
            onMounted(() => this._ensureFiscalQr());
        }

        async _ensureFiscalQr() {
            const order = this.currentOrder;
            if (!order || order.fiscal_qr_url) {
                return;
            }
            if (!order.server_id) {
                return;
            }
            try {
                const result = await jsonRpc('/mercadopago/fiscal_qr', {
                    order_uid: order.uid,
                    pos_reference: order.name,
                });
                if (result.fiscal_qr_url) {
                    order.setFiscalQrUrl(result.fiscal_qr_url);
                    this.render();
                }
            } catch (error) {
                console.warn('Fiscal QR unavailable', error); // eslint-disable-line no-console
            }
        }
    };

    Registries.Component.extend(ReceiptScreen, ReceiptScreenMp);

    const PaymentlineMp = (Paymentline) => class extends Paymentline {
        setMpPaymentData(data) {
            this.mp_payment_id = data && data.payment_id;
            this.mp_external_reference = data && data.external_reference;
            this.mp_transaction_id = data && data.transaction_id;
        }

        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.mp_payment_id = this.mp_payment_id;
            json.mp_external_reference = this.mp_external_reference;
            json.mp_transaction_id = this.mp_transaction_id;
            return json;
        }

        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.mp_payment_id = json.mp_payment_id;
            this.mp_external_reference = json.mp_external_reference;
            this.mp_transaction_id = json.mp_transaction_id;
        }
    };

    Registries.Model.extend(models.Paymentline, PaymentlineMp);

    const OrderMp = (Order) => class extends Order {
        constructor() {
            super(...arguments);
            this.fiscal_qr_url = this.fiscal_qr_url || null;
        }

        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.fiscal_qr_url = json.fiscal_qr_url || null;
        }

        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.fiscal_qr_url = this.fiscal_qr_url;
            return json;
        }

        export_for_printing() {
            const result = super.export_for_printing(...arguments);
            result.fiscal_qr_url = this.fiscal_qr_url;
            return result;
        }

        setFiscalQrUrl(url) {
            this.fiscal_qr_url = url;
        }
    };

    Registries.Model.extend(models.Order, OrderMp);
});
