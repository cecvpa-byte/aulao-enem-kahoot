const $=s=>document.querySelector(s), views=["join","physicalMode","waiting","question","done"];
let player=JSON.parse(localStorage.getItem("enemPlayer")||"null"), selected=false, shownQuestion=-1;
function view(id){views.forEach(x=>$("#"+x).classList.toggle("hidden",x!==id))}
function safe(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}
async function api(path,data){const r=await fetch(path,{method:data?"POST":"GET",headers:data?{"Content-Type":"application/json"}:{},body:data?JSON.stringify(data):undefined});const j=await r.json();if(!r.ok)throw Error(j.error||"Não foi possível concluir.");return j}
$("#joinForm").addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{player=await api("/api/join",{code:$("#roomCodeInput").value,name:$("#name").value,age:$("#age").value});localStorage.setItem("enemPlayer",JSON.stringify(player));$("#playerName").textContent=player.name;view("waiting")}catch(x){alert(x.message)}finally{b.disabled=false}});
function answer(choice,q){if(selected)return;selected=true;document.querySelectorAll(".option").forEach(b=>b.disabled=true);const fb=$("#answerFeedback");fb.classList.remove("hidden","good","bad");fb.textContent="Resposta enviada! Aguarde o resultado da pergunta.";api("/api/answer",{id:player.id,question:q,choice}).then(a=>{fb.classList.add(a.correct?"good":"bad");fb.textContent=a.correct?`✦ Boa! +${a.points.toLocaleString("pt-BR")} pontos`:"Quase! Continue ligado para a próxima."}).catch(e=>{fb.classList.add("bad");fb.textContent=e.message})}
async function refresh(){try{const s=await api("/api/state");if(player)$("#roomCode").textContent=player.code||"------";
 if(s.mode==="placards"){view("physicalMode");return}
 if(!player){view("join");return}
 if(s.state==="finished"){view("done");const m=await api("/api/me?id="+encodeURIComponent(player.id));$("#finalScore").textContent=m.score.toLocaleString("pt-BR");$("#finalAnswered").textContent=`${m.answered} de ${s.total} respondidas`;return}
 if(s.state==="question"&&s.question){view("question");if(shownQuestion!==s.current){shownQuestion=s.current;selected=false;$("#answerFeedback").classList.add("hidden");$("#questionSubject").textContent=s.question.subject.toUpperCase();$("#questionNum").textContent=`PERGUNTA ${String(s.current+1).padStart(2,"0")} / ${s.total}`;$("#questionTopic").textContent=s.question.topic.toUpperCase();$("#prompt").textContent=s.question.prompt;$("#options").replaceChildren(...s.question.options.map((text,i)=>{const b=document.createElement("button");b.className="option";b.innerHTML=`<span class="letter">${"ABCDE"[i]}</span><span>${safe(text)}</span>`;b.onclick=()=>answer(i,s.current);return b}))}}
 else {view("waiting");$("#waitText").textContent=s.current>=0?"Resposta registrada! Aguarde a próxima pergunta.":"O professor está preparando a primeira pergunta."}
 }catch(e){if(!player)view("join")}}
refresh();setInterval(refresh,1100);
