'use strict';
const $=id=>document.getElementById(id), token=document.querySelector('meta[name=coulis-token]').content;
let current=null;
const node=(tag,content)=>{const n=document.createElement(tag);n.textContent=content;return n;};
async function api(action,args={}){
 const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json','X-Coulis-Token':token},body:JSON.stringify({action,arguments:args})});
 const value=await r.json();if(!r.ok)throw Error(value.error||'Request failed');return value;
}
async function attempt(fn){$('status').textContent='';try{await fn();}catch(e){$('status').textContent=e.message;}}
function button(label,fn,secondary=false){const b=node('button',label);b.type='button';if(secondary)b.className='secondary';b.onclick=()=>attempt(async()=>{b.disabled=true;try{await fn();}finally{b.disabled=false;}});return b;}
function context(f){const c={surface:f.get('surface')};for(const k of ['audience','purpose'])if(f.get(k).trim())c[k]=f.get(k).trim();return c;}
function bind(id,fn){$(id).addEventListener('submit',e=>{e.preventDefault();attempt(async()=>{const b=e.submitter;b.disabled=true;try{await fn(new FormData(e.target));}finally{b.disabled=false;}});});}
function showComparison(c){
 current=c;$('comparison').hidden=false;$('comparison-task').textContent=c.task;
 c.candidates.forEach((d,i)=>$('candidate'+i).textContent=d.text);
 $('decide').hidden=!!c.decision;$('propose').hidden=!(c.decision&&c.decision.category==='style'&&typeof c.decision.choice==='number');
 $('decision-result').textContent=c.decision?'Decision saved. A: '+c.conditions[0]+' · B: '+c.conditions[1]+'. Preferences still require approval.':'';
 if(!c.decision)$('decide').reset();
}
async function refresh(){
 const state=await api('state');$('connection').textContent='Connected to your local profile. Decisions and approved preferences are shared with Coulis MCP. No model call is made here.';
 $('proposals').replaceChildren();for(const p of state.proposals){const card=node('article','');card.className='proposal';card.append(node('h3','Review before saving'),node('p',p.text),node('small','Context: '+JSON.stringify(p.scope)));
 card.append(button('Approve preference',async()=>{await api('approve',{proposal_id:p.id,approved:true});await refresh();$('status').textContent='Preference approved. It is now available to Coulis in this context.';}),button('Not now',async()=>{await api('reject',{proposal_id:p.id});await refresh();},true));$('proposals').append(card);}
 $('preferences').replaceChildren();if(!state.preferences.length)$('preferences').append(node('p','No approved preferences yet. Start with a style choice above.'));
 for(const p of state.preferences){const card=node('article','');card.className='preference';card.append(node('h3',p.text),node('small',(p.active?'Active':'Inactive / superseded')+' · '+JSON.stringify(p.scope)),node('small','Based on '+p.evidence_ids.length+' saved choice(s)'));
 for(const id of p.evidence_ids)card.append(button('View supporting choice',async()=>{showComparison(await api('view',{comparison_id:id}));$('comparison').scrollIntoView({behavior:'smooth'});},true));
 if(p.active){const details=node('details','');details.append(node('summary','Edit this preference'));const wording=document.createElement('input');wording.value=p.text;wording.setAttribute('aria-label','Revised preference');const value=document.createElement('input');value.value=p.value;value.setAttribute('aria-label','Revised value');details.append(wording,value,button('Review revision',async()=>{await api('revise',{preference_id:p.id,value:value.value,wording:wording.value});await refresh();}));card.append(details,button('Disable',async()=>{await api('disable',{preference_id:p.id});await refresh();},true));}
 $('preferences').append(card);}
 $('summary').textContent=state.summary.groups.length?state.summary.groups.map(g=>g.conditions.join(' vs ')+'\n'+g.conditions.map(c=>c+': '+g.wins[c]+' selected').join(' · ')+'\nTies: '+g.ties+' · Neither: '+g.neither).join('\n\n'):'No decisions yet. Your comparisons will appear here.';$('history').replaceChildren();for(const c of state.comparisons)$('history').append(button((c.decided?'Reviewed: ':'Pending: ')+c.task,async()=>showComparison(await api('view',{comparison_id:c.id})),true));
}
bind('create',async f=>{const c=await api('create',{task:f.get('task'),context:context(f),consent:f.get('consent')==='on',candidates:[{text:f.get('draft1'),condition:f.get('condition1')},{text:f.get('draft2'),condition:f.get('condition2')}]});showComparison(c);await refresh();$('comparison').scrollIntoView({behavior:'smooth'});});
bind('decide',async f=>{const raw=f.get('choice'),choice=raw==='0'||raw==='1'?Number(raw):raw;const args={comparison_id:current.id,choice,category:f.get('category'),reason:f.get('reason')};if(f.get('final').trim())args.final=f.get('final');showComparison(await api('decide',args));await refresh();});
bind('propose',async f=>{await api('propose',{comparison_id:current.id,key:f.get('key'),value:f.get('value'),wording:f.get('wording')});await refresh();});
bind('prepare',async f=>{const result=await api('prepare',{task:f.get('task'),context:context(f)});$('prepared-details').hidden=false;$('prepared-info').hidden=false;
 const info=$('prepared-info');info.replaceChildren(node('p','Ready for your model. Both conditions use the same task and writing examples. The Coulis condition adds these approved preferences:'));
 for(const p of result.coulis.preferences)info.append(node('p','• '+p.text));
 if(!result.coulis.preferences.length)info.append(node('p','No approved preferences match this context yet.'));
 if(result.coulis.conflicts.length)info.append(node('p','Resolve conflicting preferences before generating: '+result.coulis.conflicts.join(', ')));
 info.append(node('small','No drafts have been generated. Use these inputs in your connected MCP host, then compare the outputs above.'));
 $('prepared').textContent=JSON.stringify(result,null,2);});
if(token==='__TOKEN__'){
 $('connection').textContent='Run locally to use this workspace: python3 scripts/taste_loop.py --profile private/my-profile. Then open http://127.0.0.1:8767. This static page cannot save to your profile.';
 document.querySelectorAll('button').forEach(b=>b.disabled=true);
}else attempt(refresh);
