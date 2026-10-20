const $=s=>document.querySelector(s);
let pin=sessionStorage.getItem("enemPin")||"",latest=null;

async function api(path,data){
 const opt={headers:{"X-Teacher-Pin":pin}};
 if(data){opt.method="POST";opt.headers["Content-Type"]="application/json";opt.body=JSON.stringify(data)}
 const r=await fetch(path,opt),j=await r.json();if(!r.ok)throw Error(j.error||"Não foi possível concluir.");return j;
}
function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}
$("#pinForm").onsubmit=async e=>{e.preventDefault();pin=$("#pin").value;try{await api("/api/board");sessionStorage.setItem("enemPin",pin);showDash()}catch{$("#loginError").textContent="PIN inválido. Verifique o PIN privado do painel.";$("#loginError").classList.remove("hidden")}};
function showDash(){$("#login").classList.add("hidden");$("#dash").classList.remove("hidden");loadNetworkAddresses();update()}
async function loadNetworkAddresses(){try{const n=await api("/api/network"),port=n.port;if(n.public_demo){$(".local-access>span").textContent="LINK PÚBLICO DA TURMA";$("#localAddresses").innerHTML=`<div><span>TV</span><code>${esc(location.origin)}/tv</code></div>`;$(".local-access small").textContent="Abra este link na TV e nos dispositivos com acesso à internet."}else{$("#localAddresses").innerHTML=n.addresses.length?n.addresses.map(ip=>`<div><span>TABLETS</span><code>http://${ip}:${port}/</code></div><div><span>TV</span><code>http://${ip}:${port}/tv</code></div>`).join(""):"Conecte o notebook à rede Wi-Fi da sala para descobrir o endereço."}}catch{$("#localAddresses").textContent="Não foi possível detectar o endereço de rede."}}
function renderPlayers(ps){
 $("#playerCount").textContent=ps.length;const target=$("#players");
 if(!ps.length){target.innerHTML='<div class="empty-state"><span>✦</span><p>A sala está pronta.<br>Os alunos aparecem aqui ao entrar.</p></div>';return}
 const query=$("#playerFilter").value.trim().toLocaleLowerCase("pt-BR"),filtered=ps.filter(p=>p.name.toLocaleLowerCase("pt-BR").includes(query));
 if(!filtered.length){target.innerHTML='<div class="empty-state"><span>⌕</span><p>Nenhum participante encontrado.<br>Tente outro nome.</p></div>';return}
 target.innerHTML=filtered.map(p=>{const i=ps.indexOf(p);return `<div class="player-row"><span class="player-name"><i class="avatar">${i<3?["🥇","🥈","🥉"][i]:esc(p.name.trim()[0].toUpperCase())}</i>${esc(p.name)}</span><span>${p.age}</span><span>${p.answered}/11</span><span class="points">${Number(p.score).toLocaleString("pt-BR")}</span></div>`}).join("");
}
function renderTeacherQuestion(q,revealed){
 const panel=$("#teacherAnswer");
 if(!q){panel.classList.add("hidden");return}
 panel.classList.remove("hidden");
 $("#teacherAnswerBadge").textContent=`GABARITO: ${q.correct_letter}`;
 $("#teacherPrompt").textContent=q.prompt;
 $("#teacherExplanation").textContent=q.explanation;
 $("#teacherOptions").innerHTML=q.options.map((option,i)=>`<div class="teacher-option ${i===q.correct?"is-correct":""}"><span class="teacher-option-letter">${"ABCDE"[i]}</span><span>${esc(option)}</span>${i===q.correct?'<b>✓ CORRETA</b>':""}</div>`).join("");
 panel.setAttribute("aria-label",`Gabarito privado do professor. Resposta correta: ${q.correct_letter}${revealed?". Resposta já revelada para a turma.":"."}`);
}
async function update(){
 if(!pin)return;
 try{
  const b=await api("/api/board");latest=b;renderPlayers(b.players);
  const physical=b.mode==="placards",active=b.state==="question",finished=b.state==="finished",last=b.current===10;
  $("#dash").classList.toggle("placard-layout",physical);$("#playersCard").classList.toggle("hidden",physical);
  $("#copyLinkBtn").innerHTML=physical?"▣ Copiar link da TV":"⌁ Copiar link e código";$("#exportBtn").disabled=physical||!b.players.length;
  $("#tabletMode").classList.toggle("active",!physical);$("#placardMode").classList.toggle("active",physical);
  $("#tabletMode").disabled=b.public_demo||b.current>=0||b.state!=="lobby";$("#placardMode").disabled=b.current>=0||b.state!=="lobby";
  $("#modeHelp").textContent=b.public_demo?"Na demo pública, a turma joga com plaquinhas; o cadastro de alunos fica desativado.":physical?"A questão aparece na TV. A turma vota com plaquinhas A–E e você revela a correta depois.":"Cada aluno entra pelo tablet para responder e somar pontos.";
  $("#roomCode").classList.toggle("hidden",physical);$("#tvLink").classList.toggle("hidden",!physical);
  const done=Math.max(0,b.current+1);$("#progressText").textContent=`${done} / 11`;$("#progressBar").style.width=(done/11*100)+"%";
  $("#answeredCount").textContent=physical?(active?(b.revealed?"Resposta revelada. A turma já pode conferir e comentar.":"Deixe a turma conversar e levantar as plaquinhas."):"A tela da TV fica sincronizada com este painel."):(active?`${b.answered} resposta${b.answered===1?"":"s"} recebida${b.answered===1?"":"s"} nesta pergunta`:`${b.players.length} participante${b.players.length===1?"":"s"} na sala`);
  $("#stateLabel").textContent=active?(b.revealed?"RESPOSTA REVELADA":"PERGUNTA ABERTA"):finished?"FINALIZADO":"AGUARDANDO";
  $("#stateTitle").textContent=active?`Pergunta ${String(b.current+1).padStart(2,"0")}`:finished?"Aulão finalizado":"Sala aberta";
  const canOpen=!finished&&!active&&b.current<10||physical&&active&&b.revealed&&!last;
  $("#openBtn").classList.toggle("hidden",!canOpen);
  $("#openBtn").textContent=b.current<0?"▶  Abrir primeira pergunta":"▶  Abrir próxima pergunta";
  $("#revealBtn").classList.toggle("hidden",!physical||!active||b.revealed);
  $("#closeBtn").classList.toggle("hidden",physical||!active);
  $("#finishBtn").classList.toggle("hidden",finished||b.current<0||active&&!(physical&&b.revealed&&last)||!active&&physical&&!last);
  $("#finishBtn").textContent=physical?"Finalizar o aulão  →":"Ver resultado final  →";
  if(b.question){$("#liveSubject").textContent=b.question.subject.toUpperCase();$("#liveTopic").textContent=b.question.topic;}
  else if(finished){$("#liveSubject").textContent="AULÃO ENCERRADO";$("#liveTopic").textContent="Parabéns pela participação da turma!"}
  else if(b.current>=0){$("#liveSubject").textContent=physical?"QUESTÃO REVELADA":"RESPOSTAS RECEBIDAS";$("#liveTopic").textContent=`Pergunta ${b.current+1} encerrada`;}
  else{$("#liveSubject").textContent="AGUARDANDO INÍCIO";$("#liveTopic").textContent="Escolha o formato e abra a primeira pergunta."}
  renderTeacherQuestion(b.question,b.revealed);
 }catch(e){if(e.message.includes("autorizado")){pin="";sessionStorage.removeItem("enemPin");location.reload()}}
}
async function control(action,extra={}){try{await api("/api/control",{action,...extra});await update()}catch(e){alert(e.message)}}
async function setMode(mode){try{await api("/api/control",{action:"mode",mode});await update()}catch(e){alert(e.message)}}
$("#tabletMode").onclick=()=>setMode("tablets");$("#placardMode").onclick=()=>setMode("placards");
$("#openBtn").onclick=()=>control("open",{question:latest?latest.current+1:0});$("#revealBtn").onclick=()=>control("reveal");$("#closeBtn").onclick=()=>control("close");
$("#finishBtn").onclick=async()=>{await api("/api/control",{action:"finish"});await update();if(latest?.mode==="tablets")await showResults()};
$("#resetBtn").onclick=()=>{if(confirm("Começar outra partida? O placar e os dados da partida atual serão apagados."))control("start")};
$("#hideResults").onclick=()=>$("#results").classList.add("hidden");
async function showResults(){const r=await api("/api/results"),p=r.players,medals=["🥇","🥈","🥉"];
 $("#podium").innerHTML=(p.length?p.slice(0,3):[]).map((x,i)=>`<div class="podium-item"><span class="medal">${medals[i]}</span><strong>${esc(x.name)}</strong><small>${x.correct||0} acertos · ${x.answered}/11</small><b>${Number(x.score).toLocaleString("pt-BR")} pts</b></div>`).join("")||"<p>Ainda não há participantes.</p>";
 $("#questionResults").innerHTML=r.questions.map((q,i)=>`<div class="result-q"><span>QUESTÃO ${String(i+1).padStart(2,"0")}</span><strong>${esc(q.topic)}</strong><small>Gabarito: ${q.correct} &nbsp;·&nbsp; Respostas: ${Object.entries(q.answers).map(([l,n])=>l+" "+n).join(" · ")||"nenhuma"}</small></div>`).join("");$("#results").classList.remove("hidden");$("#results").scrollIntoView({behavior:"smooth",block:"start"});
}
$("#playerFilter").addEventListener("input",()=>{if(latest)renderPlayers(latest.players)});
$("#copyLinkBtn").onclick=async()=>{const text=latest?.mode==="placards"?`${location.origin}/tv`:`Acesse ${location.origin}/ e informe o código ${latest?.code||""}`;try{await navigator.clipboard.writeText(text);const b=$("#copyLinkBtn");const old=b.textContent;b.textContent="✓ Copiado!";setTimeout(()=>b.textContent=old,1600)}catch{alert(text)}};
$("#exportBtn").onclick=()=>{if(!latest?.players?.length)return;const quote=v=>'"'+String(v??"").replaceAll('"','""')+'"',rows=[["Nome","Idade","Pontos","Respondidas","Acertos"],...latest.players.map(p=>[p.name,p.age,p.score,p.answered,p.correct||0])];const csv="\uFEFF"+rows.map(row=>row.map(quote).join(";")).join("\r\n"),url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"})),a=document.createElement("a");a.href=url;a.download="resultados-aulao-enem.csv";a.click();URL.revokeObjectURL(url)};
document.addEventListener("keydown",e=>{if(e.altKey||e.ctrlKey||e.metaKey||["INPUT","TEXTAREA"].includes(document.activeElement?.tagName))return;const key=e.key.toLowerCase();if(key==="n"&&!$("#openBtn").classList.contains("hidden"))$("#openBtn").click();else if(key==="r"&&!$("#revealBtn").classList.contains("hidden"))$("#revealBtn").click();else if(e.key==="Escape"&&!$("#closeBtn").classList.contains("hidden"))$("#closeBtn").click()});
if(pin){api("/api/board").then(showDash).catch(()=>{pin="";sessionStorage.removeItem("enemPin")})}
setInterval(()=>{if(!$("#dash").classList.contains("hidden"))update()},1400);
