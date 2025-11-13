odoo.define('mezztt_mp_qr.PosModels', function (require) {
    'use strict';

    const models = require('point_of_sale.models');

    models.load_fields('pos.payment.method', ['mp_qr_enabled']);

    const PosModelSuper = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            PosModelSuper.initialize.apply(this, arguments);
            this.mezzttMpQrMethodIds = [];
        },
        after_load_server_data: function () {
            const self = this;
            return PosModelSuper.after_load_server_data.apply(this, arguments).then(function (loaded) {
                self.mezzttMpQrMethodIds = (self.payment_methods || [])
                    .filter((pm) => pm.mp_qr_enabled)
                    .map((pm) => pm.id);
                self.config.mezzttMpQrMethodIds = self.mezzttMpQrMethodIds;
                return loaded;
            });
        },
    });

    const OrderSuper = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            OrderSuper.initialize.apply(this, arguments);
            this.mezzttMpPaymentReference = null;
            this.mercadoPagoApproved = false;
        },
        export_as_JSON: function () {
            const json = OrderSuper.export_as_JSON.apply(this, arguments);
            if (this.mezzttMpPaymentReference) {
                json.mezztt_mp_payment_reference = this.mezzttMpPaymentReference;
            }
            return json;
        },
        init_from_JSON: function (json) {
            OrderSuper.init_from_JSON.apply(this, arguments);
            this.mezzttMpPaymentReference = json.mezztt_mp_payment_reference || null;
        },
        set_mezztt_mp_payment_reference: function (reference) {
            this.mezzttMpPaymentReference = reference;
        },
    });
});
