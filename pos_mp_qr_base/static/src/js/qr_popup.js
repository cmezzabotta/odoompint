
odoo.define('pos_mp_qr_base.MpQrPopup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { useState } = owl;

    const MpQrPopup = AbstractAwaitablePopup.extend({
        template: 'MpQrPopup',
        setup() {
            super.setup();
            this.state = useState({ qrData: null });
        },
        async generateQr() {
            // Placeholder: Acá se llamará al backend para obtener el QR
            this.state.qrData = 'data:image/png;base64,iVBORw0...'; // Dummy base64 img
        },
    });

    return MpQrPopup;
});
