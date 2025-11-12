/** @odoo-module **/
import { useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { AbstractAwaitablePopup } from "point_of_sale.ConfirmPopup";
import { _t } from "@web/core/l10n/translation";

export class MpQrPopup extends AbstractAwaitablePopup {
    setup(){
        super.setup();
        this.state = useState({status:'waiting',message:_t('Esperando pago...'),seconds:0});
        this._timer=null; this._poller=null;
        onWillStart(()=>this._startTimers());
        onWillUnmount(()=>this._clearTimers());
    }
    async _pollStatus(){
        const url = `/mp/mezztt/status/${encodeURIComponent(this.props.payment_id)}`;
        const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({}),credentials:'include'}).then(r=>r.json());
        if(res.status==='approved'){ this.state.status='approved'; this.state.message=_t('Recibimos tu pago'); this.render(); this.confirm(); }
    }
    _startTimers(){
        this._timer=setInterval(()=>{this.state.seconds++; if(this.state.seconds>=120)this.cancel();},1000);
        this._poller=setInterval(()=>{if(this.state.status==='waiting')this._pollStatus();},2500);
    }
    _clearTimers(){ if(this._timer)clearInterval(this._timer); if(this._poller)clearInterval(this._poller); }
    getPayload(){ return {status:this.state.status}; }
    cancel(){ this.state.status='cancelled'; this.state.message=_t('Pago cancelado'); super.cancel(); }
}
MpQrPopup.template="pos_mercado_pago_mezztt.MpQrPopup";
MpQrPopup.defaultProps={title:_t('Mercado Pago QR'),body:''};
