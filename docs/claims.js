/* Conservative approval matching for the browser demo; shared fixtures test parity. */
(function(root){
  const fields=['id','entity','metric','value','unit','time_period','source','approved_at','valid_until','statement'];
  function canonical(s){return s.toLowerCase().replace(/’/g,"'").replace(/\s+/g,' ').trim().replace(/[.!?]+$/,'').replace(/\b([0-9][0-9,]*(?:\.[0-9]+)?)(?:\s*([km]))?\b/g,(_,n,k)=>String(Number(n.replace(/,/g,''))*(k==='k'?1000:k==='m'?1000000:1)));}
  function date(s){return typeof s==='string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s)) && new Date(s).toISOString().slice(0,10)===s;}
  function validate(r){return r && fields.every(k=>r[k]!==undefined&&String(r[k]).trim()!=='') && Number.isFinite(Number(r.value)) && date(r.approved_at) && date(r.valid_until) && r.approved_at<=r.valid_until && (!r.paraphrases || (Array.isArray(r.paraphrases)&&r.paraphrases.every(s=>typeof s==='string'&&s.trim())));}
  function assess(text,records=[],today=new Date().toISOString().slice(0,10)){
    const valid=records.filter(validate), invalid=records.filter(r=>!validate(r));
    const claims=text.split(/(?<=[.!?;])\s+|\n+/).map(s=>s.trim()).filter(s=>s&&/\d|\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion)\b/i.test(s)).map(quote=>{
      const matched=valid.filter(r=>[r.statement,...(r.paraphrases||[])].some(s=>canonical(s)===canonical(quote)));
      const active=matched.filter(r=>r.approved_at<=today&&r.valid_until>=today);
      let reason='No complete approved wording matched. Review entity, metric, value, unit, period and source.',status='unresolved';
      if(matched.length&&!active.length) reason='Matching approval is expired or not yet effective.';
      if(active.length){const conflict=active.some(r=>valid.some(x=>['entity','metric','unit','time_period'].every(k=>canonical(String(r[k]))===canonical(String(x[k])))&&x.approved_at<=today&&x.valid_until>=today&&Number(x.value)!==Number(r.value)));
        if(conflict)reason='Conflicting active approvals for the same entity, metric, unit and period.';
        else{status='matched_approval';reason='Matched user-approved wording; the source has not been independently verified.';}}
      return {quote,status,reason};
    });
    return {claims,invalid_approvals:invalid,status:invalid.length||claims.some(c=>c.status==='unresolved')?'unresolved':'no_unresolved_detected',facts_verified:false};
  }
  const api={assess,validate}; if(typeof module!=='undefined')module.exports=api;else root.CoulisClaims=api;
})(typeof window!=='undefined'?window:this);
