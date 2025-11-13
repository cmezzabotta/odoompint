odoo.define('mezztt.MercadoPagoQrPopup', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl;

    class MercadoPagoQrPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            this.state = useState({
                busy: false,
                status_message: '',
                status_type: '',
                qr_image: null,
            });
            const currency = this.props.currency || 'ARS';
            const locale = this.env.pos ? this.env.pos.lang : 'es-AR';
            this.currencyFormatter = new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency,
            });
            this._pollHandle = null;
        }

        get items() {
            return (this.props.items || []).map((line) => ({
                name: line.name,
                qty: line.qty,
                price_formatted: line.price_formatted || this.currencyFormatter.format(line.price),
                total_formatted: line.total_formatted || this.currencyFormatter.format(line.qty * line.price),
            }));
        }

        get totalFormatted() {
            return this.props.total_formatted || this.currencyFormatter.format(this.props.total || 0);
        }

        async onPay() {
            if (this.state.busy) {
                return;
            }
            this.state.busy = true;
            this.state.status_message = '';
            this.state.status_type = '';
            try {
                const result = await this.rpc({
                    model: 'pos.order',
                    method: 'action_mezztt_create_qr',
                    args: [[], this.props.backendPayload],
                });
                if (result && result.qr_data) {
                    this.state.qr_image = result.qr_image || null;
                    this.state.status_message = result.message || this.env._t('Código QR generado, aguardando pago...');
                    this.state.status_type = 'success';
                    if (this.props.onPaymentCreated) {
                        this.props.onPaymentCreated(result);
                    }
                    if (result.external_reference) {
                        this._pollPayment(result.external_reference);
                    }
                } else {
                    throw new Error((result && result.error) || this.env._t('No se pudo generar el QR.'));
                }
            } catch (error) {
                console.error('Mercado Pago QR error', error);
                this.state.status_message = error.message || String(error);
                this.state.status_type = 'error';
            } finally {
                this.state.busy = false;
            }
        }

        willUnmount() {
            if (this._pollHandle) {
                clearTimeout(this._pollHandle);
                this._pollHandle = null;
            }
        }

        async _pollPayment(externalReference) {
            const self = this;
            try {
                const result = await this.rpc({
                    model: 'pos.order',
                    method: 'action_mezztt_check_payment',
                    args: [[], externalReference],
                });
                const status = result && (result.status || result.order_status || result['status_detail']);
                if (status && ['paid', 'approved', 'closed'].includes(status)) {
                    this.state.status_message = this.env._t('Pagado ✔️');
                    this.state.status_type = 'success';
                    if (this.props.onPaid) {
                        this.props.onPaid(result);
                    }
                    setTimeout(function () {
                        self.confirm();
                    }, 5000);
                    return;
                }
                if (status && ['cancelled', 'rejected'].includes(status)) {
                    this.state.status_message = this.env._t('Pago rechazado, intenta nuevamente.');
                    this.state.status_type = 'error';
                    return;
                }
            } catch (error) {
                console.warn('Mercado Pago polling error', error);
            }
            this._pollHandle = setTimeout(function () {
                self._pollPayment(externalReference);
            }, 4000);
        }
    }

    MercadoPagoQrPopup.template = 'mezztt.MercadoPagoQrPopup';
    MercadoPagoQrPopup.defaultProps = {
        confirmText: 'Cerrar',
        cancelText: 'Cancelar',
        title: 'Mercado Pago QR',
        currency: 'ARS',
    };

    Registries.Component.add('MercadoPagoQrPopup', MercadoPagoQrPopup);

    return MercadoPagoQrPopup;
});
