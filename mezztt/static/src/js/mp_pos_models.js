odoo.define('mezztt.PosModels', function (require) {
    'use strict';

    const models = require('point_of_sale.models');

    const _superPosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            _superPosModel.initialize.apply(this, arguments);
            this.set('mezztt_payment_method_id', null);
        },
        after_load_server_data: function () {
            const self = this;
            return _superPosModel.after_load_server_data.apply(this, arguments).then(function (loaded) {
                const mpMethod = self.payment_methods.find((pm) => pm.name === 'Mercado Pago QR');
                if (mpMethod) {
                    self.config.mezztt_payment_method_id = mpMethod.id;
                }
                return loaded;
            });
        },
    });

    const _superOrder = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            _superOrder.initialize.apply(this, arguments);
            this.mezzttPaymentReference = null;
        },
        export_as_JSON: function () {
            const json = _superOrder.export_as_JSON.apply(this, arguments);
            if (this.mezzttPaymentReference) {
                json.mezztt_payment_reference = this.mezzttPaymentReference;
            }
            return json;
        },
        init_from_JSON: function (json) {
            _superOrder.init_from_JSON.apply(this, arguments);
            this.mezzttPaymentReference = json.mezztt_payment_reference || null;
        },
        set_mezztt_payment_reference: function (reference) {
            this.mezzttPaymentReference = reference;
        },
    });
});
