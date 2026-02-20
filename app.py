from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import random

NUMERO_LIMITE = 100

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="troque-essa-chave-por-uma-forte")

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/img", StaticFiles(directory="img"), name="img")

# ---- Catálogo de jogos ----
GAMES = [
    {
        "id": "numero-secreto",
        "title": "Número Secreto",
        "description": "Adivinhe o número de 1 a 100 com dicas de maior/menor.",
        "path": "/games/numero-secreto",
        "cover": "/img/capa-numero-secreto.png",
        "badge": "Python + FastAPI",
    },
    {
        "id": "sorteador",
        "title": "Sorteador de Números",
        "description": "Sorteie números únicos dentro de um intervalo, com validações.",
        "path": "/games/sorteador",
        "cover": "/img/capa-sorteador.png",
        "badge": "Python + FastAPI",
    },

    {
    "id": "amigo-secreto",
    "title": "Amigo Secreto",
    "description": "Adicione amigos e sorteie os pares do amigo secreto.",
    "path": "/games/amigo-secreto",
    "cover": "/img/capa-amigo-secreto.png",  
    "badge": "Python + FastAPI",
    },

    { "id": "truco",
      "title": "Truco ♣ ♥ ♠ ♦ ",
      "description": "Um Truco de baralho limpo, enfrente o bot, escolha suas cartas e vença as rodadas com estratégia.",
      "path": "/games/truco", 
      "cover": "/img/img-truco/capa-truco.png", 
      "badge": "Python + FastAPI", 
    },

]


# -------------------- NUMERO SECRETO --------------------
def _ns_ensure_state(request: Request) -> None:
    """Estado por sessão do jogo 'numero-secreto'."""
    s = request.session
    s.setdefault("ns_pool", [])
    s.setdefault("ns_secret", None)
    s.setdefault("ns_tries", 1)

    if not isinstance(s["ns_pool"], list) or len(s["ns_pool"]) == 0:
        pool = list(range(1, NUMERO_LIMITE + 1))
        random.shuffle(pool)
        s["ns_pool"] = pool

    if not isinstance(s["ns_secret"], int):
        s["ns_secret"] = s["ns_pool"].pop()

    if not isinstance(s["ns_tries"], int):
        s["ns_tries"] = 1


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "games": GAMES}
    )


@app.get("/games/numero-secreto", response_class=HTMLResponse)
def numero_secreto_page(request: Request):
    _ns_ensure_state(request)
    return templates.TemplateResponse(
        "games/numero_secreto.html",
        {"request": request}
    )


@app.post("/api/numero-secreto/novo-jogo")
def ns_novo_jogo(request: Request):
    _ns_ensure_state(request)
    s = request.session

    if len(s["ns_pool"]) == 0:
        pool = list(range(1, NUMERO_LIMITE + 1))
        random.shuffle(pool)
        s["ns_pool"] = pool

    s["ns_secret"] = s["ns_pool"].pop()
    s["ns_tries"] = 1

    return JSONResponse({
        "ok": True,
        "titulo": "Jogo do número secreto",
        "mensagem": f"Escolha um número entre 1 e {NUMERO_LIMITE}",
        "reiniciar_habilitado": False,
    })


@app.post("/api/numero-secreto/chute")
async def ns_chute(request: Request):
    _ns_ensure_state(request)
    s = request.session

    body = await request.json()
    chute = body.get("chute")

    try:
        chute = int(chute)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "erro": "Envie um número válido."}, status_code=400)

    if chute < 1 or chute > NUMERO_LIMITE:
        return JSONResponse({"ok": False, "erro": f"O chute deve estar entre 1 e {NUMERO_LIMITE}."}, status_code=400)

    secret = s["ns_secret"]
    tries = s["ns_tries"]

    if chute == secret:
        palavra = "tentativa" if tries == 1 else "tentativas"
        return JSONResponse({
            "ok": True,
            "acertou": True,
            "titulo": "Acertou!",
            "mensagem": f"Você descobriu o número secreto com {tries} {palavra}!",
            "reiniciar_habilitado": True,
        })

    s["ns_tries"] = tries + 1
    dica = "O número secreto é menor" if chute > secret else "O número secreto é maior"

    return JSONResponse({
        "ok": True,
        "acertou": False,
        "titulo": None,
        "mensagem": dica,
        "reiniciar_habilitado": False,
    })


# -------------------- SORTEADOR --------------------
@app.get("/games/sorteador", response_class=HTMLResponse)
def sorteador_page(request: Request):
    return templates.TemplateResponse(
        "games/sorteador.html",
        {"request": request}
    )


@app.post("/api/sorteador/sortear")
async def sorteador_sortear(request: Request):
    body = await request.json()
    quantidade = body.get("quantidade")
    de = body.get("de")
    ate = body.get("ate")

    try:
        quantidade = int(quantidade)
        de = int(de)
        ate = int(ate)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "erro": "Preencha todos os campos com números válidos."}, status_code=400)

    if quantidade <= 0:
        return JSONResponse({"ok": False, "erro": "A quantidade deve ser maior que zero."}, status_code=400)

    if de > ate:
        return JSONResponse({"ok": False, "erro": 'O valor "Do número" não pode ser maior que "Até o número".'}, status_code=400)

    total_possiveis = ate - de + 1
    if quantidade > total_possiveis:
        return JSONResponse(
            {"ok": False, "erro": f"Quantidade ({quantidade}) maior que o total de números possíveis no intervalo ({total_possiveis})."},
            status_code=400
        )

    sorteados = random.sample(range(de, ate + 1), k=quantidade)
    return JSONResponse({"ok": True, "sorteados": sorteados})

# -------------------- AMIGO SECRETO --------------------
import uuid

def _as_ensure_state(request: Request) -> None:
    s = request.session
    s.setdefault("as_friends", [])
    if not isinstance(s["as_friends"], list):
        s["as_friends"] = []

    # migração simples caso você já tenha lista de strings salva
    if s["as_friends"] and isinstance(s["as_friends"][0], str):
        s["as_friends"] = [{"id": uuid.uuid4().hex, "name": n} for n in s["as_friends"]]


@app.get("/games/amigo-secreto", response_class=HTMLResponse)
def amigo_secreto_page(request: Request):
    _as_ensure_state(request)
    return templates.TemplateResponse(
        "games/amigo_secreto.html",
        {"request": request}
    )


@app.get("/api/amigo-secreto/estado")
def amigo_secreto_estado(request: Request):
    _as_ensure_state(request)
    return JSONResponse({"ok": True, "amigos": request.session["as_friends"]})


@app.post("/api/amigo-secreto/adicionar")
async def amigo_secreto_adicionar(request: Request):
    _as_ensure_state(request)
    s = request.session

    body = await request.json()
    nome = (body.get("nome") or "").strip()

    if not nome:
        return JSONResponse({"ok": False, "erro": "Digite um nome válido."}, status_code=400)

    # evita duplicado (case-insensitive)
    ja_existe = any(item["name"].lower() == nome.lower() for item in s["as_friends"])
    if ja_existe:
        return JSONResponse({"ok": False, "erro": "Esse nome já foi adicionado."}, status_code=400)

    s["as_friends"].append({"id": uuid.uuid4().hex, "name": nome})
    return JSONResponse({"ok": True, "amigos": s["as_friends"]})


@app.post("/api/amigo-secreto/editar")
async def amigo_secreto_editar(request: Request):
    _as_ensure_state(request)
    s = request.session

    body = await request.json()
    friend_id = (body.get("id") or "").strip()
    novo_nome = (body.get("nome") or "").strip()

    if not friend_id:
        return JSONResponse({"ok": False, "erro": "ID inválido."}, status_code=400)
    if not novo_nome:
        return JSONResponse({"ok": False, "erro": "Digite um nome válido."}, status_code=400)

    # encontra amigo
    alvo = next((item for item in s["as_friends"] if item["id"] == friend_id), None)
    if not alvo:
        return JSONResponse({"ok": False, "erro": "Amigo não encontrado."}, status_code=404)

    # evita duplicado com outros (case-insensitive)
    ja_existe = any(
        item["id"] != friend_id and item["name"].lower() == novo_nome.lower()
        for item in s["as_friends"]
    )
    if ja_existe:
        return JSONResponse({"ok": False, "erro": "Esse nome já existe na lista."}, status_code=400)

    alvo["name"] = novo_nome
    return JSONResponse({"ok": True, "amigos": s["as_friends"]})


@app.post("/api/amigo-secreto/remover")
async def amigo_secreto_remover(request: Request):
    _as_ensure_state(request)
    s = request.session

    body = await request.json()
    friend_id = (body.get("id") or "").strip()
    if not friend_id:
        return JSONResponse({"ok": False, "erro": "ID inválido."}, status_code=400)

    antes = len(s["as_friends"])
    s["as_friends"] = [item for item in s["as_friends"] if item["id"] != friend_id]

    if len(s["as_friends"]) == antes:
        return JSONResponse({"ok": False, "erro": "Amigo não encontrado."}, status_code=404)

    return JSONResponse({"ok": True, "amigos": s["as_friends"]})


@app.post("/api/amigo-secreto/sortear")
def amigo_secreto_sortear(request: Request):
    _as_ensure_state(request)
    s = request.session

    amigos = s["as_friends"]
    if len(amigos) < 4:
        return JSONResponse({"ok": False, "erro": "Adicione pelo menos 4 amigos para sortear."}, status_code=400)

    embaralhado = amigos[:]
    random.shuffle(embaralhado)

    pares = []
    for i in range(len(embaralhado)):
        atual = embaralhado[i]["name"]
        proximo = embaralhado[0]["name"] if i == len(embaralhado) - 1 else embaralhado[i + 1]["name"]
        pares.append({"de": atual, "para": proximo})

    return JSONResponse({"ok": True, "pares": pares})


@app.post("/api/amigo-secreto/reiniciar")
def amigo_secreto_reiniciar(request: Request):
    _as_ensure_state(request)
    request.session["as_friends"] = []
    return JSONResponse({"ok": True, "amigos": []})

# --- Sobre mim --- 

@app.get("/sobre")
def sobre(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request}
    )

# =========================
# 🃏 TRUCO (PAULISTA SIMPLIFICADO) — TURNO 100% CORRETO + TRUCO/6/9/12 + MANILHA CORRETA
# =========================

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
import random

TRUCO_NAIPES = ["♣", "♥", "♠", "♦"]  # usado só para montar as cartas/arquivos
TRUCO_ORDEM = ["Q", "J", "K", "A", "2", "3"]  # ranking base (sem manilha)
TRUCO_VALORES = [1, 3, 6, 9, 12]  # escada do truco

# ✅ Truco Paulista (manilha): ZAP(♣) > COPAS(♥) > ESPADAS(♠) > OUROS(♦)
# Para comparar: número MAIOR = mais forte
TRUCO_FORCA_MANILHA = {"♦": 1, "♠": 2, "♥": 3, "♣": 4}


# ⭐ ROTA DA PÁGINA
@app.get("/games/truco", response_class=HTMLResponse)
def truco_page(request: Request):
    return templates.TemplateResponse("games/truco.html", {"request": request})


# ----------------- FUNÇÕES BASE -----------------

def prox_valor(atual: int):
    i = TRUCO_VALORES.index(atual)
    return TRUCO_VALORES[i + 1] if i < len(TRUCO_VALORES) - 1 else None

def truco_parse(carta: str):
    # carta é tipo "Q♣", "3♦"
    return carta[:-1], carta[-1]

def truco_proxima(rank: str):
    # manilha = próxima do vira
    return TRUCO_ORDEM[(TRUCO_ORDEM.index(rank) + 1) % len(TRUCO_ORDEM)]

def truco_baralho():
    # baralho limpo (24 cartas)
    d = [f"{r}{n}" for r in TRUCO_ORDEM for n in TRUCO_NAIPES]
    random.shuffle(d)
    return d

def truco_poder(carta: str, manilha_rank: str):
    r, n = truco_parse(carta)
    if r == manilha_rank:
        # manilha sempre ganha de qualquer não-manilha
        return (100, TRUCO_FORCA_MANILHA[n])
    # quanto maior o índice, mais forte (Q mais fraco ... 3 mais forte)
    return (TRUCO_ORDEM.index(r), 0)

def truco_comparar(a: str, b: str, manilha_rank: str):
    pa = truco_poder(a, manilha_rank)
    pb = truco_poder(b, manilha_rank)
    return (pa > pb) - (pa < pb)


# ----------------- IA DO BOT -----------------

def bot_escolher_resposta(mao_bot, carta_user, manilha_rank):
    """
    Bot tenta ganhar gastando o mínimo:
    - Se tiver alguma que ganha, joga a menor que ganha
    - Senão, joga a menor da mão
    """
    ganhadoras = [c for c in mao_bot if truco_comparar(c, carta_user, manilha_rank) == 1]
    if ganhadoras:
        return min(ganhadoras, key=lambda c: truco_poder(c, manilha_rank))
    return min(mao_bot, key=lambda c: truco_poder(c, manilha_rank))

def bot_escolher_torno(mao_bot, manilha_rank):
    """
    Quando o bot vai 'tornar' (jogar primeiro na rodada),
    joga uma carta mediana/baixa pra guardar as fortes.
    """
    ordenadas = sorted(mao_bot, key=lambda c: truco_poder(c, manilha_rank))
    if len(ordenadas) == 3:
        return ordenadas[1]
    return ordenadas[0]

def bot_deve_pedir_truco(g):
    """
    Bot só pode pedir na vez dele, antes de jogar.
    Estratégia simples: chance de pedir se tiver carta forte (manilha ou 3).
    """
    if g["pedido"] is not None:
        return False
    if g["mao_valor"] >= 12:
        return False
    if g["vez"] != "bot":
        return False
    if g["carta_bot_mesa"] is not None:
        return False

    fortes = 0
    for c in g["mao_bot"]:
        r, _ = truco_parse(c)
        if r == g["manilha"]:
            fortes += 2
        elif r == "3":
            fortes += 1

    if fortes >= 2:
        chance = 0.35
    elif fortes == 1:
        chance = 0.18
    else:
        chance = 0.06

    return random.random() < chance

def bot_responde_pedido(g, novo_valor):
    """
    Bot decide se aceita, corre ou aumenta.
    """
    proximo = prox_valor(novo_valor)
    pode_aumentar = proximo is not None

    if novo_valor >= 9:
        p_correr = 0.28
        p_aumentar = 0.10 if pode_aumentar else 0.0
    elif novo_valor >= 6:
        p_correr = 0.18
        p_aumentar = 0.18 if pode_aumentar else 0.0
    else:
        p_correr = 0.10
        p_aumentar = 0.22 if pode_aumentar else 0.0

    x = random.random()
    if x < p_correr:
        return "correr"
    if x < p_correr + p_aumentar:
        return "aumentar"
    return "aceitar"


# ----------------- ESTADO DO JOGO -----------------

def novo_estado(placar_user=0, placar_bot=0, mao_inicial="user"):
    deck = truco_baralho()
    vira = deck.pop()
    manilha = truco_proxima(truco_parse(vira)[0])

    g = {
        "deck": deck,
        "vira": vira,
        "manilha": manilha,

        "mao_user": [deck.pop() for _ in range(3)],
        "mao_bot": [deck.pop() for _ in range(3)],

        "placar_user": placar_user,
        "placar_bot": placar_bot,

        "tricks": [],                 # "user" / "bot" / "tie"
        "mao_inicial": mao_inicial,   # quem é "mão" desta mão
        "vez": mao_inicial,           # quem joga agora (se "bot", ele pode tornar)
        "carta_bot_mesa": None,       # quando bot torna, carta fica na mesa

        # ✅ quem iniciou a rodada atual (importante para empates)
        "rodada_iniciador": mao_inicial,

        "mao_valor": 1,
        "pedido": None,               # {"por":"bot"/"user", "base":X, "valor":Y}
        "finalizado": False
    }
    return g

def ensure_truco(request: Request):
    if "truco" not in request.session or not isinstance(request.session["truco"], dict):
        request.session["truco"] = novo_estado()

def placar_list(g):
    return [g["placar_user"], g["placar_bot"]]

def fim_de_jogo(g):
    return g["placar_user"] >= 12 or g["placar_bot"] >= 12

def mensagem_fim(g):
    if g["placar_user"] >= 12:
        return "FIM DE JOGO — Você venceu! 🏆"
    return "FIM DE JOGO — Bot venceu!"

def vencedor_da_mao(tricks, mao_inicial):
    """
    Regras resumidas:
    - Quem ganhar 2 rodadas vence a mão
    - Empate + vitória em alguma das duas primeiras já decide
    - 3 empates => mão (mao_inicial) vence
    """
    u = tricks.count("user")
    b = tricks.count("bot")
    t = tricks.count("tie")

    if u >= 2:
        return "user"
    if b >= 2:
        return "bot"

    if len(tricks) >= 2 and t >= 1:
        if u == 1 and b == 0:
            return "user"
        if b == 1 and u == 0:
            return "bot"

    if len(tricks) == 3:
        if u > b:
            return "user"
        if b > u:
            return "bot"
        return mao_inicial

    return None

def iniciar_nova_mao(request: Request, mao_inicial: str):
    g_old = request.session["truco"]
    pu, pb = g_old["placar_user"], g_old["placar_bot"]
    request.session["truco"] = novo_estado(placar_user=pu, placar_bot=pb, mao_inicial=mao_inicial)

def bot_torna_se_precisar(g):
    """
    Se for vez do bot, sem pedido pendente, ele pode:
    - pedir truco (antes de jogar)
    - ou tornar (jogar carta na mesa)
    Retorna a carta tornada (ou None).
    """
    if g["finalizado"]:
        return None
    if g["pedido"] is not None:
        return None
    if g["vez"] != "bot":
        return None

    # pedir truco antes de jogar
    if bot_deve_pedir_truco(g):
        proximo = prox_valor(g["mao_valor"])
        if proximo:
            g["pedido"] = {"por": "bot", "base": g["mao_valor"], "valor": proximo}
            # continua sendo vez do bot, mas aguardando resposta do user
            return None

    # se já tem carta na mesa, só garante que a vez é do user
    if g["carta_bot_mesa"] is not None:
        g["vez"] = "user"
        return g["carta_bot_mesa"]

    if not g["mao_bot"]:
        return None

    carta = bot_escolher_torno(g["mao_bot"], g["manilha"])
    g["mao_bot"].remove(carta)
    g["carta_bot_mesa"] = carta

    # ✅ rodada foi iniciada pelo bot
    g["rodada_iniciador"] = "bot"

    # agora você responde
    g["vez"] = "user"
    return carta


# ----------------- NOVO JOGO -----------------

@app.get("/api/truco/new")
def truco_new(request: Request):
    request.session["truco"] = novo_estado(placar_user=0, placar_bot=0, mao_inicial="user")
    g = request.session["truco"]

    return {
        "ok": True,
        "vira": g["vira"],
        "mao_user": g["mao_user"],
        "placar": placar_list(g),
        "vez": g["vez"],
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido"],
        "manilha": g["manilha"],
        "fim_jogo": False,
        "bot_iniciou": None
    }


# ----------------- PEDIR TRUCO (USER) -----------------

@app.post("/api/truco/pedir")
def truco_pedir(request: Request):
    ensure_truco(request)
    g = request.session["truco"]

    if g["finalizado"] or fim_de_jogo(g):
        g["finalizado"] = True
        request.session["truco"] = g
        return {"ok": True, "fim_jogo": True, "placar": placar_list(g), "vez": g["vez"], "mensagem": mensagem_fim(g)}

    if g["pedido"] is not None:
        return JSONResponse({"ok": False, "erro": "Já existe um pedido pendente."}, 400)

    if g["vez"] != "user":
        return JSONResponse({"ok": False, "erro": "Você só pode pedir na sua vez."}, 400)

    proximo = prox_valor(g["mao_valor"])
    if not proximo:
        return JSONResponse({"ok": False, "erro": "Mão já está no máximo."}, 400)

    acao = bot_responde_pedido(g, proximo)

    if acao == "correr":
        g["placar_user"] += g["mao_valor"]

        if fim_de_jogo(g):
            g["finalizado"] = True
            request.session["truco"] = g
            return {"ok": True, "fim_jogo": True, "placar": placar_list(g), "vez": g["vez"], "mensagem": mensagem_fim(g)}

        iniciar_nova_mao(request, mao_inicial="user")
        g2 = request.session["truco"]
        bot_iniciou = bot_torna_se_precisar(g2)
        request.session["truco"] = g2

        return {
            "ok": True,
            "mensagem": f"Bot correu! Você ganhou {g['mao_valor']} ponto(s).",
            "nova_mao": True,
            "vira": g2["vira"],
            "mao_user": g2["mao_user"],
            "placar": placar_list(g2),
            "mao_valor": g2["mao_valor"],
            "pedido": g2["pedido"],
            "manilha": g2["manilha"],
            "vez": g2["vez"],
            "fim_jogo": False,
            "bot_iniciou": bot_iniciou
        }

    if acao == "aceitar":
        g["mao_valor"] = proximo
        request.session["truco"] = g
        return {
            "ok": True,
            "mensagem": f"Bot aceitou! Mão valendo {g['mao_valor']}.",
            "placar": placar_list(g),
            "mao_valor": g["mao_valor"],
            "pedido": g["pedido"],
            "manilha": g["manilha"],
            "vez": g["vez"],
            "fim_jogo": False,
            "bot_iniciou": None
        }

    proximo2 = prox_valor(proximo)
    if not proximo2:
        g["mao_valor"] = proximo
        request.session["truco"] = g
        return {
            "ok": True,
            "mensagem": f"Bot aceitou! Mão valendo {g['mao_valor']}.",
            "placar": placar_list(g),
            "mao_valor": g["mao_valor"],
            "pedido": g["pedido"],
            "manilha": g["manilha"],
            "vez": g["vez"],
            "fim_jogo": False,
            "bot_iniciou": None
        }

    g["pedido"] = {"por": "bot", "base": g["mao_valor"], "valor": proximo2}
    request.session["truco"] = g
    return {
        "ok": True,
        "mensagem": f"Bot aumentou pra {proximo2}! Aceita, corre ou aumenta?",
        "placar": placar_list(g),
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido"],
        "manilha": g["manilha"],
        "vez": g["vez"],
        "fim_jogo": False,
        "bot_iniciou": None
    }


# ----------------- AUMENTAR (USER responde pedido do BOT) -----------------

@app.post("/api/truco/aumentar")
def truco_aumentar(request: Request):
    ensure_truco(request)
    g = request.session["truco"]

    if g["pedido"] is None or g["pedido"]["por"] != "bot":
        return JSONResponse({"ok": False, "erro": "Não há pedido do bot para aumentar."}, 400)

    valor_atual_pedido = g["pedido"]["valor"]
    proximo = prox_valor(valor_atual_pedido)
    if not proximo:
        return JSONResponse({"ok": False, "erro": "Não dá para aumentar mais."}, 400)

    acao = bot_responde_pedido(g, proximo)

    if acao == "correr":
        g["placar_user"] += valor_atual_pedido
        g["pedido"] = None

        if fim_de_jogo(g):
            g["finalizado"] = True
            request.session["truco"] = g
            return {"ok": True, "fim_jogo": True, "placar": placar_list(g), "vez": g["vez"], "mensagem": mensagem_fim(g)}

        iniciar_nova_mao(request, mao_inicial="user")
        g2 = request.session["truco"]
        bot_iniciou = bot_torna_se_precisar(g2)
        request.session["truco"] = g2

        return {
            "ok": True,
            "mensagem": f"Bot correu! Você ganhou {valor_atual_pedido} ponto(s).",
            "nova_mao": True,
            "vira": g2["vira"],
            "mao_user": g2["mao_user"],
            "placar": placar_list(g2),
            "mao_valor": g2["mao_valor"],
            "pedido": g2["pedido"],
            "manilha": g2["manilha"],
            "vez": g2["vez"],
            "fim_jogo": False,
            "bot_iniciou": bot_iniciou
        }

    if acao == "aceitar":
        g["mao_valor"] = proximo
        g["pedido"] = None

        bot_card = bot_torna_se_precisar(g)
        request.session["truco"] = g

        return {
            "ok": True,
            "mensagem": f"Bot aceitou! Mão valendo {g['mao_valor']}.",
            "placar": placar_list(g),
            "mao_valor": g["mao_valor"],
            "pedido": g["pedido"],
            "manilha": g["manilha"],
            "vez": g["vez"],
            "fim_jogo": False,
            "bot_iniciou": bot_card
        }

    proximo2 = prox_valor(proximo)
    if not proximo2:
        g["mao_valor"] = proximo
        g["pedido"] = None
        bot_card = bot_torna_se_precisar(g)
        request.session["truco"] = g
        return {
            "ok": True,
            "mensagem": f"Bot aceitou! Mão valendo {g['mao_valor']}.",
            "placar": placar_list(g),
            "mao_valor": g["mao_valor"],
            "pedido": g["pedido"],
            "manilha": g["manilha"],
            "vez": g["vez"],
            "fim_jogo": False,
            "bot_iniciou": bot_card
        }

    g["pedido"] = {"por": "bot", "base": g["mao_valor"], "valor": proximo2}
    request.session["truco"] = g
    return {
        "ok": True,
        "mensagem": f"Bot aumentou pra {proximo2}! Aceita, corre ou aumenta?",
        "placar": placar_list(g),
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido"],
        "manilha": g["manilha"],
        "vez": g["vez"],
        "fim_jogo": False,
        "bot_iniciou": None
    }


# ----------------- ACEITAR (USER aceita pedido do BOT) -----------------

@app.post("/api/truco/aceitar")
def truco_aceitar(request: Request):
    ensure_truco(request)
    g = request.session["truco"]

    if g["pedido"] is None or g["pedido"]["por"] != "bot":
        return JSONResponse({"ok": False, "erro": "Não há pedido do bot para aceitar."}, 400)

    g["mao_valor"] = g["pedido"]["valor"]
    g["pedido"] = None

    bot_card = bot_torna_se_precisar(g)
    request.session["truco"] = g

    return {
        "ok": True,
        "mensagem": f"Aceito! Mão valendo {g['mao_valor']}.",
        "placar": placar_list(g),
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido"],
        "manilha": g["manilha"],
        "vez": g["vez"],
        "fim_jogo": False,
        "bot_iniciou": bot_card
    }


# ----------------- CORRER (USER corre do pedido do BOT) -----------------

@app.post("/api/truco/correr")
def truco_correr(request: Request):
    ensure_truco(request)
    g = request.session["truco"]

    if g["pedido"] is None or g["pedido"]["por"] != "bot":
        return JSONResponse({"ok": False, "erro": "Não há pedido do bot para correr."}, 400)

    base = g["pedido"]["base"]
    g["placar_bot"] += base
    g["pedido"] = None

    if fim_de_jogo(g):
        g["finalizado"] = True
        request.session["truco"] = g
        return {"ok": True, "fim_jogo": True, "placar": placar_list(g), "vez": g["vez"], "mensagem": mensagem_fim(g)}

    iniciar_nova_mao(request, mao_inicial="bot")
    g2 = request.session["truco"]
    bot_card = bot_torna_se_precisar(g2)
    request.session["truco"] = g2

    return {
        "ok": True,
        "mensagem": f"Você correu! Bot ganhou {base} ponto(s).",
        "nova_mao": True,
        "vira": g2["vira"],
        "mao_user": g2["mao_user"],
        "placar": placar_list(g2),
        "mao_valor": g2["mao_valor"],
        "pedido": g2["pedido"],
        "manilha": g2["manilha"],
        "vez": g2["vez"],
        "fim_jogo": False,
        "bot_iniciou": bot_card
    }


# ----------------- JOGAR CARTA (USER) -----------------

@app.post("/api/truco/play")
async def truco_play(request: Request):
    ensure_truco(request)
    g = request.session["truco"]

    if g["finalizado"] or fim_de_jogo(g):
        g["finalizado"] = True
        request.session["truco"] = g
        return {"ok": True, "fim_jogo": True, "placar": placar_list(g), "vez": g["vez"], "mensagem": mensagem_fim(g)}

    if g["pedido"] is not None:
        return JSONResponse({"ok": False, "erro": "Responda ao pedido (Aceitar/Correr/Aumentar) antes de jogar."}, 400)

    body = await request.json()
    carta_user = body.get("carta")

    if g["vez"] != "user":
        return JSONResponse({"ok": False, "erro": "Espere o bot jogar."}, 400)

    if not carta_user or carta_user not in g["mao_user"]:
        return JSONResponse({"ok": False, "erro": "Carta inválida."}, 400)

    # ✅ define quem iniciou a rodada atual:
    # - se o bot já tinha tornado (carta na mesa), iniciador = bot
    # - senão, iniciador = user
    rodada_iniciador = "bot" if g["carta_bot_mesa"] is not None else "user"
    g["rodada_iniciador"] = rodada_iniciador

    # 1) user joga
    g["mao_user"].remove(carta_user)

    # 2) carta do bot
    if g["carta_bot_mesa"] is not None:
        carta_bot = g["carta_bot_mesa"]
        g["carta_bot_mesa"] = None
    else:
        if not g["mao_bot"]:
            return JSONResponse({"ok": False, "erro": "Bot sem carta disponível."}, 400)
        carta_bot = bot_escolher_resposta(g["mao_bot"], carta_user, g["manilha"])
        g["mao_bot"].remove(carta_bot)

    # 3) resolve a rodada
    r = truco_comparar(carta_user, carta_bot, g["manilha"])

    if r == 1:
        g["tricks"].append("user")
        vencedor_rodada = "user"
    elif r == -1:
        g["tricks"].append("bot")
        vencedor_rodada = "bot"
    else:
        g["tricks"].append("tie")
        vencedor_rodada = "tie"

    # 4) define quem "torna" a próxima rodada
    if vencedor_rodada == "user":
        g["vez"] = "user"
    elif vencedor_rodada == "bot":
        g["vez"] = "bot"
    else:
        # ✅ empate: mantém iniciador da rodada
        g["vez"] = g["rodada_iniciador"]

    # 5) verifica vencedor da mão
    win = vencedor_da_mao(g["tricks"], g["mao_inicial"])
    if win is not None:
        if win == "user":
            g["placar_user"] += g["mao_valor"]
        elif win == "bot":
            g["placar_bot"] += g["mao_valor"]

        if fim_de_jogo(g):
            g["finalizado"] = True
            request.session["truco"] = g
            return {
                "ok": True,
                "sua_carta": carta_user,
                "carta_bot": carta_bot,
                "resultado_rodada": "venceu" if r == 1 else ("perdeu" if r == -1 else "empatou"),
                "placar": placar_list(g),
                "mao_valor": g["mao_valor"],
                "pedido": g["pedido"],
                "manilha": g["manilha"],
                "vez": g["vez"],
                "fim_jogo": True,
                "mensagem": mensagem_fim(g),
                "nova_mao": False,
                "bot_iniciou": None
            }

        # ✅ quem ganhou a mão é mão na próxima
        iniciar_nova_mao(request, mao_inicial=win)
        g2 = request.session["truco"]

        bot_iniciou = bot_torna_se_precisar(g2)  # se bot for mão, ele torna
        request.session["truco"] = g2

        return {
            "ok": True,
            "sua_carta": carta_user,
            "carta_bot": carta_bot,
            "resultado_rodada": "venceu" if r == 1 else ("perdeu" if r == -1 else "empatou"),
            "placar": placar_list(g2),
            "vira": g2["vira"],
            "mao_user": g2["mao_user"],
            "mao_valor": g2["mao_valor"],
            "pedido": g2["pedido"],
            "manilha": g2["manilha"],
            "vez": g2["vez"],
            "fim_jogo": False,
            "nova_mao": True,
            "bot_iniciou": bot_iniciou
        }

    # 6) se a próxima vez for do bot, ele torna automaticamente (ou pede truco)
    bot_iniciou = None
    if g["vez"] == "bot" and g["pedido"] is None and not g["finalizado"] and not fim_de_jogo(g):
        bot_iniciou = bot_torna_se_precisar(g)
        # se ele tornou, g["vez"] vira "user" e a carta fica na mesa
        # se ele pediu truco, "pedido" fica preenchido e a vez permanece do bot aguardando sua resposta

    request.session["truco"] = g

    return {
        "ok": True,
        "sua_carta": carta_user,
        "carta_bot": carta_bot,
        "resultado_rodada": "venceu" if r == 1 else ("perdeu" if r == -1 else "empatou"),
        "placar": placar_list(g),
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido"],
        "manilha": g["manilha"],
        "vez": g["vez"],
        "fim_jogo": False,
        "nova_mao": False,
        "bot_iniciou": bot_iniciou
    }