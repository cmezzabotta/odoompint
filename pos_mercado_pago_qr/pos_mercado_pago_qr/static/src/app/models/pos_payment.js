/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";

patch(PosPayment.prototype, {
    async pay() {
        this.set_payment_status("waiting");
        const paymentTerminal = this.payment_method_id.payment_terminal;
        if (!paymentTerminal || typeof paymentTerminal.send_payment_request !== "function") {
            throw new Error("La terminal de pago no está disponible para Mercado Pago QR.");
        }
        const paymentRequest = this._exportMercadoPagoRequest();
        const isPaymentSuccessful = await paymentTerminal.send_payment_request(paymentRequest);
        return this.handle_payment_response(isPaymentSuccessful);
    },

    _exportMercadoPagoRequest() {
        const order = this.pos_order_id;
        const exported = typeof order?.export_for_printing === "function" ? order.export_for_printing() : null;
        const partner = order?.partner_id;
        const customer = partner
            ? {
                  id: partner.id || (Array.isArray(partner) ? partner[0] : undefined),
                  name:
                      partner.name ||
                      partner.display_name ||
                      (Array.isArray(partner) ? partner[1] : undefined) ||
                      undefined,
                  email: partner.email || undefined,
              }
            : undefined;
        const lines = exported?.orderlines || exported?.lines || [];
        const items = Array.isArray(lines)
            ? lines.map((line, index) => {
                  const quantity = Math.abs(parseFloat(line.qty ?? line.quantity ?? 1) || 1);
                  const unitPrice = Math.abs(
                      parseFloat(
                          line.price_unit ??
                              line.price ??
                              line.price_with_tax ??
                              line.price_without_tax ??
                              line.total_with_tax ??
                              0
                      ) || 0
                  );
                  const category = line.pos_categ_id || line.category_id;
                  const categoryId = Array.isArray(category) ? category[0] : category;
                  return {
                      title: line.product_name || line.name || `Item ${index + 1}`,
                      description: line.product_name || line.name,
                      quantity,
                      unit_price: unitPrice,
                      unit_measure: line.unit_measure || line.uom || "unit",
                      external_code: line.default_code || line.product_code || line.code || null,
                      external_categories: categoryId ? [{ id: String(categoryId) }] : [],
                  };
              })
            : [];

        const currency = order?.currency
            ? typeof order.currency === "object"
                ? order.currency.name || order.currency.symbol || order.currency.iso_code
                : order.currency
            : undefined;

        return {
            paymentLineUuid: this.uuid,
            amount: this.get_amount(),
            reference: order?.name || order?.pos_reference || order?.uuid,
            description: exported?.note || exported?.name,
            currency,
            customer,
            items,
            metadata: {
                order_id: order?.id,
            },
            expiration_minutes: this.payment_method_id?.mpqr_order_validity,
            external_pos_id: this.payment_method_id?.mpqr_pos_external_id,
            store_id: this.payment_method_id?.mpqr_store_id,
            integrator_id: this.payment_method_id?.mpqr_integrator_id,
        };
    },
});
