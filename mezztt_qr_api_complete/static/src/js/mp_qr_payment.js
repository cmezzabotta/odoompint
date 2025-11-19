
odoo.define('mezztt_qr_api_complete.mpqr', function(require){
    "use strict";

    const { Component, useState, useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    class MPQRPayment extends PaymentScreen {
        async validateOrder(isForceValidate){
            const order = this.currentOrder;
            const config = this.env.pos.config;

            if (order.selected_paymentline.payment_method.name !== "QR Mercado Pago") {
                return super.validateOrder(isForceValidate);
            }

            const amount = order.get_total_with_tax();
            const order_ref = order.uid;
            const config_id = config.id;

            const qr = config.mp_static_qr_url;

            // Create Order
            const mp_order = await this.rpc({
                route: '/mpqr/create_order',
                params: { amount, order_ref, config_id }
            });

            const mp_order_id = mp_order.get("id") || mp_order["id"];
            if (!mp_order_id){
                return;
            }

            await this.showPopup('ConfirmPopup',{
                title:"Escanee el QR",
                body:"Esperando pago..."
            });

            // Polling
            let paid = false;
            const start = Date.now();

            while(!paid){
                if (Date.now() - start > 180000){
                    await this.showPopup('ErrorPopup',{
                        title:"Tiempo excedido",
                        body:"El pago no fue recibido."
                    });
                    this.trigger('close-temp-screen');
                    this.showScreen('ProductScreen');
                    return;
                }

                const st = await this.rpc({
                    route:'/mpqr/check_status',
                    params:{order_id:mp_order_id, config_id}
                });

                if(st.status === "paid"){
                    paid = true;
                }

                await new Promise(r=>setTimeout(r,2000));
            }

            return super.validateOrder(isForceValidate);
        }
    }

    Registries.Component.extend(PaymentScreen, MPQRPayment);
    return MPQRPayment;
});
