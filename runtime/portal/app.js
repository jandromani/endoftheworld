const $=s=>document.querySelector(s);
function humanBytes(n){if(n==null)return"—";let x=n,u=["B","KB","MB","GB","TB"],i=0;while(x>=1000&&i<u.length-1){x/=1000;i++}return x.toFixed(i?1:0)+" "+u[i]}
function serviceUrl(port){return location.protocol+"//"+location.hostname+":"+port+"/"}
document.querySelectorAll(".service").forEach(a=>a.href=serviceUrl(a.dataset.port));
async function refresh(){try{const s=await fetch("/api/status",{cache:"no-store"}).then(r=>r.json());$("#net").textContent=s.internet?"Internet reachable":"Offline mode";$("#netDot").classList.toggle("off",!s.internet);$("#node").textContent=s.node;$("#storage").textContent=humanBytes(s.storage.free)+" free";$("#health").textContent=s.services.knowledge&&s.services.ai&&s.services.voice?"READY":"DEGRADED";let t="Portal <b>UP</b><br>Kiwix <b>"+(s.services.knowledge?"UP":"DOWN")+"</b><br>AI <b>"+(s.services.ai?"UP":"DOWN")+"</b><br>Voice <b>"+(s.services.voice?"UP":"DOWN")+"</b><br>Map <b>"+(s.map_ready?"READY":"MISSING")+"</b>";if(s.battery.present)t+="<br>Battery <b>"+(s.battery.percent??"?")+"%</b>";$("#services").innerHTML=t}catch(e){$("#net").textContent="status unavailable";$("#netDot").classList.add("off")}}
async function apps(){try{const rows=await fetch("/api/apps").then(r=>r.json());$("#apps").innerHTML=rows.length?rows.map(a=>'<a class="btn" href="'+a.url+'">'+a.name.replace(/\.apk$/i,"")+" · "+humanBytes(a.bytes)+"</a>").join(""):'<span class="muted">No APKs frozen.</span>'}catch(e){$("#apps").textContent="unavailable"}}
function capHref(action){if(!action)return null;if(action.kind==="service")return serviceUrl(action.port);return action.href||null}
async function capabilities(){
  const root=$("#capabilities");
  try{
    const rows=await fetch("/api/capabilities",{cache:"no-store"}).then(r=>r.json());
    root.replaceChildren();
    if(!rows.length){root.textContent="No frozen capability index available.";root.classList.add("muted");return}
    for(const c of rows){
      const row=document.createElement("div");row.className="cap-row";
      const left=document.createElement("div");
      const name=document.createElement("div");name.className="cap-name";name.textContent=c.id;
      const meta=document.createElement("div");meta.className="cap-meta";meta.textContent=[c.family,c.kind,c.bytes!=null?humanBytes(c.bytes):null].filter(Boolean).join(" · ");
      if(c.note){const note=document.createElement("div");note.className="cap-meta";note.textContent=c.note;left.append(name,meta,note)}else left.append(name,meta);
      const right=document.createElement("div");const state=document.createElement("div");state.className="cap-state";state.textContent=c.state;right.appendChild(state);
      const href=capHref(c.action);if(href){const a=document.createElement("a");a.className="cap-action";a.href=href;a.textContent=c.action.label||"Open";right.appendChild(a)}
      row.append(left,right);root.appendChild(row);
    }
  }catch(e){root.textContent="Capability index unavailable: "+e.message;root.classList.add("muted")}
}
let messages=[{role:"system",content:"You are the local ENDWORLD NANO assistant. Be concise, practical, and distinguish uncertainty. You are running fully offline."}];
function addMsg(text,cls=""){const d=document.createElement("div");d.className="msg "+cls;d.textContent=text;$("#chatlog").appendChild(d);$("#chatlog").scrollTop=$("#chatlog").scrollHeight;return d}
async function send(){const p=$("#prompt"),q=p.value.trim();if(!q)return;p.value="";messages.push({role:"user",content:q});addMsg(q,"user");const wait=addMsg("Thinking locally…");$("#send").disabled=true;try{const data=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages})}).then(async r=>{const j=await r.json();if(!r.ok)throw new Error(j.error||r.statusText);return j});const answer=data.choices?.[0]?.message?.content||JSON.stringify(data);wait.textContent=answer;messages.push({role:"assistant",content:answer})}catch(e){wait.textContent="AI unavailable: "+e.message}finally{$("#send").disabled=false}}
$("#send").addEventListener("click",send);$("#prompt").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}});setInterval(()=>$("#clock").textContent=new Date().toLocaleString(),1000);refresh();apps();capabilities();setInterval(refresh,15000);

async function transcribe(){
  const f=$("#audioFile").files?.[0];if(!f){$("#transcript").textContent="Choose an audio file first.";return}
  const b=$("#transcribe");b.disabled=true;$("#transcript").textContent="Transcribing locally…";
  const form=new FormData();form.append("file",f);form.append("response_format","json");form.append("temperature","0.0");
  try{
    const r=await fetch("/api/transcribe",{method:"POST",body:form});const data=await r.json();
    if(!r.ok)throw new Error(data.error||r.statusText);
    $("#transcript").textContent=data.text||data.transcription||JSON.stringify(data);
  }catch(e){$("#transcript").textContent="Transcription unavailable: "+e.message}
  finally{b.disabled=false}
}
$("#transcribe").addEventListener("click",transcribe);
