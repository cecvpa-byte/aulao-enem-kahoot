"""Local classroom Kahoot-style quiz server. No external services required."""
from __future__ import annotations

import hmac
import ipaddress
import json
import os
import secrets
import socket
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "kahoot.sqlite3")))
PIN_PATH = ROOT / "professor.pin"
APP = Flask(__name__, static_folder="static")
APP.config["MAX_CONTENT_LENGTH"] = 32 * 1024
DB_LOCK = threading.RLock()
LETTERS = "ABCDE"
SERVER_PORT = int(os.getenv("PORT", "5055"))
PUBLIC_DEMO_MODE = os.getenv("PUBLIC_DEMO_MODE", "0").strip() == "1"
DEFAULT_MODE = "placards" if PUBLIC_DEMO_MODE else "tablets"

def load_pin():
    configured = os.getenv("KAHOOT_ADMIN_PIN", "").strip()
    if configured:
        return configured
    if PIN_PATH.exists():
        return PIN_PATH.read_text(encoding="utf-8").strip()
    generated = secrets.token_urlsafe(9).replace("-", "A").replace("_", "B")[:12]
    PIN_PATH.write_text(generated, encoding="utf-8")
    return generated

PIN = load_pin()

QUESTIONS = [
    {"subject":"História","topic":"Pré-História e Revolução Neolítica","prompt":"Durante milhares de anos, diferentes grupos humanos desenvolveram ferramentas, dominaram o fogo e criaram estratégias de sobrevivência. Posteriormente, a agricultura e a domesticação de animais favoreceram mudanças na organização das comunidades.\n\nUma consequência importante da chamada Revolução Neolítica foi:","options":["O desaparecimento imediato das atividades de caça e coleta.","A formação de comunidades sedentárias e o desenvolvimento da produção de alimentos.","A criação das primeiras fábricas e do trabalho assalariado.","O surgimento dos grandes impérios industriais.","O fim das diferenças sociais entre os grupos humanos."],"correct":1},
    {"subject":"História","topic":"Grécia e Roma Antigas","prompt":"Na Grécia Antiga, a democracia ateniense permitia a participação de cidadãos nas decisões políticas. Entretanto, mulheres, pessoas escravizadas e estrangeiros não possuíam os mesmos direitos políticos. Em Roma, a participação política também foi marcada por disputas entre diferentes grupos sociais.\n\nA análise dessas sociedades permite concluir que:","options":["A democracia antiga garantia igualdade política a todos os habitantes.","A cidadania era um direito universal nas sociedades greco-romanas.","A participação política era limitada por critérios sociais e jurídicos.","As sociedades antigas não possuíam conflitos políticos.","A escravidão foi inexistente nas sociedades da Antiguidade."],"correct":2},
    {"subject":"História","topic":"África e reinos africanos","prompt":"Antes e durante a expansão marítima europeia, sociedades africanas desenvolveram reinos, cidades, redes comerciais e formas próprias de organização política. O Império do Mali, por exemplo, destacou-se pelo comércio transaariano e pela riqueza associada ao ouro e ao sal.\n\nEsse contexto histórico demonstra que:","options":["A África não possuía organização política antes da colonização europeia.","Todas as sociedades africanas viviam isoladas e sem comércio.","A história africana começou com a chegada dos portugueses.","Diferentes sociedades africanas construíram estruturas políticas, econômicas e culturais complexas.","O comércio africano dependia exclusivamente dos países europeus."],"correct":3},
    {"subject":"História","topic":"Reforma e Contrarreforma","prompt":"No século XVI, críticas à Igreja Católica contribuíram para o surgimento de movimentos reformistas cristãos. A Reforma Protestante provocou mudanças religiosas e políticas na Europa, enquanto a Igreja Católica promoveu ações de renovação e reafirmação de suas doutrinas.\n\nUma consequência desses movimentos foi:","options":["A unificação religiosa definitiva de toda a Europa.","O fim imediato das disputas entre católicos e protestantes.","A fragmentação da cristandade ocidental e o fortalecimento de conflitos religiosos e políticos.","O desaparecimento do poder político dos monarcas europeus.","A proibição de todas as práticas religiosas cristãs."],"correct":2},
    {"subject":"História","topic":"Expansão marítima e colonização","prompt":"A expansão marítima europeia, iniciada no século XV, ampliou as rotas comerciais entre Europa, África, Ásia e América. Esse processo também envolveu conquistas territoriais, escravização de populações e exploração de recursos naturais.\n\nUma interpretação histórica desse processo é que ele:","options":["Estabeleceu relações comerciais sempre igualitárias entre os povos.","Impediu a expansão dos interesses econômicos das monarquias europeias.","Eliminou as diferenças de poder entre europeus, africanos e americanos.","Produziu somente intercâmbios culturais pacíficos.","Ampliou as conexões entre continentes, mas também aprofundou relações de dominação e exploração."],"correct":4},
    {"subject":"Filosofia","topic":"Surgimento da Filosofia","prompt":"Na Grécia Antiga, pensadores começaram a questionar explicações tradicionais sobre a origem do universo e os fenômenos naturais. Em vez de aceitar apenas narrativas míticas, passaram a investigar princípios e apresentar argumentos racionais.\n\nEssa transformação está relacionada:","options":["À busca de explicações racionais e à prática da argumentação.","À proibição de questionar as tradições.","À rejeição de toda forma de pensamento crítico.","À substituição imediata da religião pela ciência moderna.","Ao abandono de qualquer reflexão sobre a natureza."],"correct":0},
    {"subject":"Filosofia","topic":"Filosofia pré-socrática","prompt":"Heráclito afirmava que a realidade está em constante transformação, enquanto outros filósofos antigos procuravam compreender o princípio fundamental de todas as coisas.\n\nA concepção de Heráclito destaca:","options":["A impossibilidade de qualquer mudança.","A permanência absoluta de todas as coisas.","A transformação como característica fundamental da realidade.","A ideia de que os sentidos nunca apresentam mudanças.","A inexistência de relações entre os contrários."],"correct":2},
    {"subject":"Filosofia","topic":"Filosofias de diferentes tradições","prompt":"A reflexão filosófica não se desenvolveu exclusivamente na Grécia. Na China antiga, Confúcio discutiu a conduta moral, o respeito nas relações humanas e as responsabilidades de quem governa.\n\nEsse exemplo permite compreender que a Filosofia:","options":["Existe apenas nas sociedades que adotaram a democracia grega.","Pode surgir em diferentes tradições culturais e refletir sobre questões éticas e políticas.","É incompatível com a reflexão sobre a vida em sociedade.","Tem como único objetivo explicar fenômenos naturais.","Depende exclusivamente do pensamento dos filósofos europeus modernos."],"correct":1},
    {"subject":"Sociologia","topic":"Surgimento da Sociologia","prompt":"A Revolução Industrial e a Revolução Francesa transformaram o trabalho, as cidades, as relações políticas e a organização social. No século XIX, esses processos contribuíram para o desenvolvimento da Sociologia.\n\nA nova ciência surgiu, entre outros objetivos, para:","options":["Defender que as sociedades permanecem sempre iguais.","Substituir a investigação social por explicações exclusivamente religiosas.","Estudar somente as características biológicas dos indivíduos.","Compreender cientificamente as transformações e os problemas da vida em sociedade.","Impedir a análise das desigualdades sociais."],"correct":3},
    {"subject":"Sociologia","topic":"Auguste Comte e o positivismo","prompt":"Auguste Comte defendia que a sociedade poderia ser estudada de maneira sistemática, procurando identificar regularidades nos fenômenos sociais. Seu pensamento contribuiu para a consolidação da Sociologia.\n\nEssa perspectiva está associada:","options":["Ao positivismo e à valorização do conhecimento científico.","À rejeição de qualquer observação da realidade social.","À ideia de que as sociedades não podem ser estudadas.","À explicação dos problemas sociais exclusivamente pela vontade individual.","À defesa de que toda mudança social é impossível."],"correct":0},
    {"subject":"Sociologia","topic":"Émile Durkheim e os fatos sociais","prompt":"Em uma sociedade, as pessoas aprendem regras de convivência, normas jurídicas e costumes que já existiam antes de seu nascimento. Essas regras influenciam o comportamento individual e podem gerar sanções quando são desrespeitadas.\n\nPara Émile Durkheim, esse exemplo se relaciona ao conceito de:","options":["Luta de classes.","Mais-valia.","Fato social.","Alienação econômica.","Contrato natural."],"correct":2},
]

def db():
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=20000")
    return con

@contextmanager
def connection():
    con = db()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init():
    with DB_LOCK, connection() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
        CREATE TABLE IF NOT EXISTS game (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL, current INTEGER NOT NULL, opened REAL, code TEXT NOT NULL, updated REAL NOT NULL, mode TEXT NOT NULL DEFAULT 'tablets', revealed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS players (id TEXT PRIMARY KEY, name TEXT NOT NULL, age INTEGER NOT NULL, score INTEGER NOT NULL DEFAULT 0, joined REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS answers (player_id TEXT NOT NULL, question INTEGER NOT NULL, choice INTEGER NOT NULL, correct INTEGER NOT NULL, points INTEGER NOT NULL, answered REAL NOT NULL, PRIMARY KEY(player_id,question), FOREIGN KEY(player_id) REFERENCES players(id));
        """)
        cols = {row[1] for row in con.execute("PRAGMA table_info(game)").fetchall()}
        if "mode" not in cols:
            con.execute("ALTER TABLE game ADD COLUMN mode TEXT NOT NULL DEFAULT 'tablets'")
        if "revealed" not in cols:
            con.execute("ALTER TABLE game ADD COLUMN revealed INTEGER NOT NULL DEFAULT 0")
        if not con.execute("SELECT 1 FROM game WHERE id=1").fetchone():
            con.execute("INSERT INTO game(id,state,current,opened,code,updated,mode,revealed) VALUES(1,'lobby',-1,NULL,?,?,?,0)", (f"{secrets.randbelow(900000)+100000}", time.time(), DEFAULT_MODE))

def game():
    with connection() as con:
        return dict(con.execute("SELECT * FROM game WHERE id=1").fetchone())

def admin_ok():
    pin = request.headers.get("X-Teacher-Pin", "")
    return hmac.compare_digest(pin, PIN)

def err(message, status=400):
    return jsonify(error=message), status

@APP.get("/")
def student(): return send_from_directory(ROOT / "static", "index.html")

@APP.get("/professor")
def teacher(): return send_from_directory(ROOT / "static", "professor.html")

@APP.get("/tv")
def tv(): return send_from_directory(ROOT / "static", "tv.html")

@APP.get("/api/network")
def network_addresses():
    found = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = ipaddress.ip_address(item[4][0])
            if address.is_private and not address.is_loopback and not address.is_link_local:
                found.add(str(address))
    except OSError:
        pass
    return jsonify(addresses=sorted(found), port=SERVER_PORT)

@APP.get("/healthz")
def health():
    return jsonify(ok=True)

@APP.get("/api/state")
def state():
    g = game()
    qidx = g["current"]
    q = QUESTIONS[qidx] if 0 <= qidx < len(QUESTIONS) else None
    public_q = ({k: q[k] for k in ("subject", "topic", "prompt", "options")} if q else None)
    if public_q and g["revealed"]:
        public_q["correct"] = q["correct"]
    return jsonify(state=g["state"], mode=g["mode"], revealed=bool(g["revealed"]), total=len(QUESTIONS), current=qidx, question=public_q if g["state"] == "question" else None,
                   completed=(g["state"] == "finished"), server_time=time.time())

@APP.post("/api/join")
def join():
    g = game()
    if PUBLIC_DEMO_MODE or g["mode"] != "tablets": return err("Esta partida está usando plaquinhas na TV.", 409)
    body = request.get_json(silent=True) or {}
    room_code = str(body.get("code", "")).strip()
    if not hmac.compare_digest(room_code, g["code"]): return err("Código da sala inválido.", 403)
    name = " ".join(str(body.get("name", "")).split())[:48]
    try: age = int(body.get("age", 0))
    except (TypeError, ValueError): age = 0
    if len(name) < 2 or age < 5 or age > 100: return err("Informe um nome e uma idade válida.")
    pid = secrets.token_urlsafe(18)
    with DB_LOCK, connection() as con:
        con.execute("INSERT INTO players(id,name,age,joined) VALUES(?,?,?,?)", (pid, name, age, time.time()))
    return jsonify(id=pid, name=name, code=g["code"]), 201

@APP.post("/api/answer")
def answer():
    body = request.get_json(silent=True) or {}
    pid = str(body.get("id", ""))[:80]
    try: choice = int(body.get("choice", -1)); qidx = int(body.get("question", -1))
    except (TypeError, ValueError): return err("Resposta inválida.")
    if choice not in range(5): return err("Escolha uma alternativa.")
    with DB_LOCK, connection() as con:
        g = dict(con.execute("SELECT * FROM game WHERE id=1").fetchone())
        if g["mode"] != "tablets" or g["state"] != "question" or g["revealed"] or qidx != g["current"]: return err("Esta pergunta já foi encerrada.", 409)
        if not con.execute("SELECT 1 FROM players WHERE id=?", (pid,)).fetchone(): return err("Participante não encontrado.", 404)
        correct = int(choice == QUESTIONS[qidx]["correct"])
        elapsed = max(0, time.time() - (g["opened"] or time.time()))
        points = (1000 + max(0, int(500 * (1 - min(elapsed, 25) / 25)))) if correct else 0
        try:
            con.execute("INSERT INTO answers VALUES(?,?,?,?,?,?)", (pid,qidx,choice,correct,points,time.time()))
        except sqlite3.IntegrityError: return err("Você já respondeu esta pergunta.", 409)
        con.execute("UPDATE players SET score=score+? WHERE id=?", (points,pid))
    return jsonify(ok=True, correct=bool(correct), points=points)

@APP.get("/api/me")
def me():
    pid=request.args.get("id","")[:80]
    with connection() as con:
        row=con.execute("SELECT p.id,p.name,p.score,COUNT(a.question) AS answered FROM players p LEFT JOIN answers a ON a.player_id=p.id WHERE p.id=? GROUP BY p.id",(pid,)).fetchone()
    if not row: return err("Participante não encontrado.",404)
    return jsonify(dict(row))

@APP.get("/api/board")
def board():
    if not admin_ok(): return err("Acesso não autorizado.",401)
    with connection() as con:
        rows=con.execute("SELECT p.id,p.name,p.age,p.score,COUNT(a.question) AS answered,SUM(a.correct) AS correct FROM players p LEFT JOIN answers a ON a.player_id=p.id GROUP BY p.id ORDER BY p.score DESC,p.joined ASC").fetchall()
        g=dict(con.execute("SELECT * FROM game WHERE id=1").fetchone())
        answered=con.execute("SELECT COUNT(*) FROM answers WHERE question=?",(g["current"],)).fetchone()[0] if g["current"]>=0 else 0
    return jsonify(players=[dict(x) for x in rows], state=g["state"], current=g["current"], code=g["code"], mode=g["mode"], revealed=bool(g["revealed"]), total=len(QUESTIONS), question_count=len(QUESTIONS), answered=answered)

@APP.get("/api/results")
def results():
    if not admin_ok(): return err("Acesso não autorizado.",401)
    with connection() as con:
        rows=con.execute("SELECT p.name,p.age,p.score,COUNT(a.question) answered,SUM(a.correct) correct FROM players p LEFT JOIN answers a ON a.player_id=p.id GROUP BY p.id ORDER BY p.score DESC,p.joined ASC").fetchall()
        detail=[]
        for i,q in enumerate(QUESTIONS):
            stats=con.execute("SELECT choice,COUNT(*) n FROM answers WHERE question=? GROUP BY choice",(i,)).fetchall()
            detail.append({"topic":q["topic"],"correct":LETTERS[q["correct"]],"answers":{LETTERS[r["choice"]]:r["n"] for r in stats}})
    return jsonify(players=[dict(x) for x in rows], questions=detail)

@APP.post("/api/control")
def control():
    if not admin_ok(): return err("Acesso não autorizado.",401)
    action=(request.get_json(silent=True) or {}).get("action")
    with DB_LOCK, connection() as con:
        g=dict(con.execute("SELECT * FROM game WHERE id=1").fetchone())
        if action=="mode":
            mode=(request.get_json(silent=True) or {}).get("mode")
            if mode not in ("tablets", "placards"): return err("Modo inválido.")
            if PUBLIC_DEMO_MODE and mode != "placards": return err("A demonstração pública usa somente plaquinhas e não coleta dados de alunos.", 403)
            if g["state"] != "lobby" or g["current"] != -1: return err("O modo só pode ser escolhido antes de abrir a primeira pergunta.", 409)
            con.execute("UPDATE game SET mode=?,updated=? WHERE id=1",(mode,time.time()))
        elif action=="start":
            con.execute("DELETE FROM answers"); con.execute("DELETE FROM players")
            con.execute("UPDATE game SET state='lobby',current=-1,opened=NULL,revealed=0,mode=?,code=?,updated=? WHERE id=1",(DEFAULT_MODE,f"{secrets.randbelow(900000)+100000}",time.time()))
        elif action=="open":
            idx=int((request.get_json(silent=True) or {}).get("question",0))
            if idx not in range(len(QUESTIONS)): return err("Pergunta inválida.")
            can_advance = g["state"] == "lobby" or (g["mode"] == "placards" and g["state"] == "question" and g["revealed"])
            if not can_advance or idx != g["current"] + 1: return err("A próxima pergunta não está disponível.", 409)
            con.execute("UPDATE game SET state='question',current=?,opened=?,revealed=0,updated=? WHERE id=1",(idx,time.time(),time.time()))
        elif action=="reveal":
            if g["mode"] != "placards" or g["state"] != "question": return err("Não há uma pergunta de plaquinhas aberta.", 409)
            con.execute("UPDATE game SET revealed=1,updated=? WHERE id=1",(time.time(),))
        elif action=="close": con.execute("UPDATE game SET state='lobby',opened=NULL,updated=? WHERE id=1",(time.time(),))
        elif action=="finish": con.execute("UPDATE game SET state='finished',opened=NULL,revealed=1,updated=? WHERE id=1",(time.time(),))
        elif action=="reset":
            con.execute("DELETE FROM answers"); con.execute("DELETE FROM players")
            con.execute("UPDATE game SET state='lobby',current=-1,opened=NULL,revealed=0,mode=?,code=?,updated=? WHERE id=1",(DEFAULT_MODE,f"{secrets.randbelow(900000)+100000}",time.time()))
        else: return err("Ação inválida.")
    return jsonify(ok=True)

def main():
    global SERVER_PORT
    port = SERVER_PORT = int(os.getenv("PORT", "5055"))
    init()
    print("\nKAHOOT AULÃO DO ENEM — servidor local iniciado")
    print(f"Painel do professor: http://localhost:{port}/professor")
    if os.getenv("KAHOOT_ADMIN_PIN", "").strip():
        print("PIN do professor: configurado de forma segura por variável de ambiente")
    else:
        print(f"PIN do professor: {PIN}")
    print("Tablets: conecte-os à mesma rede Wi-Fi do notebook e abra o endereço IP do notebook na porta 5055.\n")
    APP.run(host="0.0.0.0",port=port,threaded=True,use_reloader=False)

init()

if __name__=="__main__": main()

