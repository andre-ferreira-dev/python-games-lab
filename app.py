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
# ✅ TRUCO COMPLETO (1/3/6/9/12)
# =========================

TRUCO_NAIPES = ["♣", "♥", "♠", "♦"]
TRUCO_ORDEM = ["Q", "J", "K", "A", "2", "3"]
TRUCO_FORCA_MANILHA = {"♣": 1, "♥": 2, "♠": 3, "♦": 4}

TRUCO_VALORES = [1, 3, 6, 9, 12]

def prox_valor(atual: int):
    i = TRUCO_VALORES.index(atual)
    return TRUCO_VALORES[i + 1] if i < len(TRUCO_VALORES) - 1 else None

def truco_parse(carta: str):
    return carta[:-1], carta[-1]

def truco_proxima(rank: str):
    return TRUCO_ORDEM[(TRUCO_ORDEM.index(rank) + 1) % len(TRUCO_ORDEM)]

def truco_baralho():
    baralho = [f"{r}{n}" for r in TRUCO_ORDEM for n in TRUCO_NAIPES]
    random.shuffle(baralho)
    return baralho

def truco_poder(carta: str, manilha: str):
    r, n = truco_parse(carta)

    if r == manilha:
        return (100, TRUCO_FORCA_MANILHA[n])

    return (TRUCO_ORDEM.index(r), 0)

def truco_comparar(a: str, b: str, manilha: str):
    pa = truco_poder(a, manilha)
    pb = truco_poder(b, manilha)
    if pa > pb:
        return 1
    if pa < pb:
        return -1
    return 0

def truco_maior_da_mao(mao: list[str], manilha: str):
    if not mao:
        return None
    return max(mao, key=lambda c: truco_poder(c, manilha))

def _truco_avaliar_forca_bot(g: dict) -> float:
    mao_bot = g.get("mao_bot", [])
    manilha = g.get("manilha")
    if not mao_bot or not manilha:
        return 0.0

    maior = truco_maior_da_mao(mao_bot, manilha)
    if not maior:
        return 0.0

    p = truco_poder(maior, manilha)

    if p[0] == 100:
        return min(1.0, 0.75 + (p[1] * 0.06))

    idx = p[0]
    return max(0.0, min(1.0, (idx / 5) * 0.65))

def novo_estado():
    deck = truco_baralho()
    vira = deck.pop()
    manilha = truco_proxima(truco_parse(vira)[0])

    return {
        "deck": deck,
        "vira": vira,
        "manilha": manilha,
        "mao_user": [deck.pop() for _ in range(3)],
        "mao_bot": [deck.pop() for _ in range(3)],

        "placar_user": 0,
        "placar_bot": 0,

        "rodada_user": 0,
        "rodada_bot": 0,
        "jogadas_na_mao": 0,

        "vencedor_rodada1": None,
        "empate_rodada1": False,
        "vantagem_empate1": None,

        # ✅ truco (valor e pendência)
        "mao_valor": 1,
        # pedido_pendente: {"por":"user"/"bot", "base":valor_atual, "valor":valor_pedido}
        "pedido_pendente": None,

        "finalizado": False
    }

def _nova_mao_mantendo_placar(request: Request, g: dict):
    novo = novo_estado()
    novo["placar_user"] = g["placar_user"]
    novo["placar_bot"] = g["placar_bot"]
    request.session["truco"] = novo
    return novo

def _aplicar_corrida(request: Request, g: dict, ganhador: str, pontos: int):
    if ganhador == "user":
        g["placar_user"] += pontos
    else:
        g["placar_bot"] += pontos

    g["pedido_pendente"] = None

    if g["placar_user"] >= 12 or g["placar_bot"] >= 12:
        g["finalizado"] = True
        request.session["truco"] = g
        return {"fim_jogo": True, "nova_mao": False, "g": g}

    novo = _nova_mao_mantendo_placar(request, g)
    return {"fim_jogo": False, "nova_mao": True, "g": novo}

def _bot_responder_pedido(request: Request, g: dict, base: int, valor_pedido: int):
    """
    Bot recebe um pedido (base -> valor_pedido) e decide:
    - correr (quem pediu ganha base)
    - aceitar (mão vale valor_pedido)
    - aumentar (mão vira valor_pedido e pendente próximo)
    """
    forca = _truco_avaliar_forca_bot(g)
    roll = random.random()

    # corre mais quando fraco
    chance_correr = 0.55 - (forca * 0.40)

    # aumenta mais quando forte e se existir próximo
    prox = prox_valor(valor_pedido)
    pode_aumentar = prox is not None
    chance_aumentar = 0.10 + (forca * 0.35)

    if roll < chance_correr:
        # bot corre => quem pediu (user) ganha base
        res = _aplicar_corrida(request, g, "user", base)
        gg = res["g"]
        return JSONResponse({
            "ok": True,
            "acao": "bot_correu",
            "mensagem": f"Bot correu! Você ganhou {base} ponto(s).",
            "nova_mao": res["nova_mao"],
            "fim_jogo": res["fim_jogo"],
            "vira": gg.get("vira"),
            "manilha": gg.get("manilha"),
            "mao_user": gg.get("mao_user"),
            "placar": [gg["placar_user"], gg["placar_bot"]],
            "mao_valor": gg.get("mao_valor", 1),
            "pedido": gg.get("pedido_pendente"),
        })

    if pode_aumentar and roll < chance_correr + chance_aumentar:
        # bot aumenta: aceita valor_pedido e pede prox
        g["mao_valor"] = valor_pedido
        g["pedido_pendente"] = {"por": "bot", "base": valor_pedido, "valor": prox}
        request.session["truco"] = g
        return JSONResponse({
            "ok": True,
            "acao": "bot_aumentou",
            "mensagem": f"Bot pediu {prox}! Aceita, corre ou aumenta?",
            "placar": [g["placar_user"], g["placar_bot"]],
            "mao_valor": g["mao_valor"],
            "pedido": g["pedido_pendente"],
        })

    # aceita
    g["mao_valor"] = valor_pedido
    g["pedido_pendente"] = None
    request.session["truco"] = g
    return JSONResponse({
        "ok": True,
        "acao": "bot_aceitou",
        "mensagem": f"Bot aceitou! Mão valendo {valor_pedido}.",
        "placar": [g["placar_user"], g["placar_bot"]],
        "mao_valor": g["mao_valor"],
        "pedido": None,
    })


@app.get("/games/truco", response_class=HTMLResponse)
def truco_page(request: Request):
    return templates.TemplateResponse("games/truco.html", {"request": request})


@app.get("/api/truco/new")
def truco_new(request: Request):
    request.session["truco"] = novo_estado()
    g = request.session["truco"]

    return JSONResponse({
        "ok": True,
        "vira": g["vira"],
        "manilha": g["manilha"],
        "mao_user": g["mao_user"],
        "placar": [g["placar_user"], g["placar_bot"]],
        "mao_valor": g["mao_valor"],
        "pedido": g["pedido_pendente"],
    })


# =========================
# ✅ PEDIR / AUMENTAR (USER)
# =========================

@app.post("/api/truco/pedir")
def truco_pedir(request: Request):
    g = request.session.get("truco")
    if not g:
        return JSONResponse({"ok": False, "erro": "Jogo não iniciado."}, status_code=400)
    if g.get("finalizado"):
        return JSONResponse({"ok": False, "erro": "Jogo finalizado."}, status_code=400)
    if g.get("pedido_pendente"):
        return JSONResponse({"ok": False, "erro": "Existe um pedido pendente. Responda (aceitar/correr/aumentar)."}, status_code=400)

    atual = int(g.get("mao_valor", 1))
    nxt = prox_valor(atual)
    if not nxt:
        return JSONResponse({"ok": False, "erro": "A mão já está valendo 12."}, status_code=400)

    # user pediu: bot responde agora
    g["pedido_pendente"] = {"por": "user", "base": atual, "valor": nxt}
    # bot responde (correr/aceitar/aumentar)
    return _bot_responder_pedido(request, g, base=atual, valor_pedido=nxt)


@app.post("/api/truco/aumentar")
def truco_aumentar(request: Request):
    """
    Usado quando o BOT pediu um valor e o USER quer aumentar (contra-pedir).
    Ex: bot pediu 6, user aumenta pra 9.
    """
    g = request.session.get("truco")
    if not g:
        return JSONResponse({"ok": False, "erro": "Jogo não iniciado."}, status_code=400)
    if g.get("finalizado"):
        return JSONResponse({"ok": False, "erro": "Jogo finalizado."}, status_code=400)

    ped = g.get("pedido_pendente")
    if not ped:
        return JSONResponse({"ok": False, "erro": "Não há pedido pendente."}, status_code=400)
    if ped.get("por") != "bot":
        return JSONResponse({"ok": False, "erro": "Você só pode aumentar quando o bot pediu."}, status_code=400)

    # Aceita o pedido atual do bot e pede o próximo
    valor_atual_pedido = int(ped["valor"])
    proximo = prox_valor(valor_atual_pedido)
    if not proximo:
        return JSONResponse({"ok": False, "erro": "Não dá para aumentar além de 12."}, status_code=400)

    # mão passa a valer o valor que o bot pediu
    g["mao_valor"] = valor_atual_pedido

    # agora o user pede o próximo, e o bot responde
    g["pedido_pendente"] = {"por": "user", "base": valor_atual_pedido, "valor": proximo}
    return _bot_responder_pedido(request, g, base=valor_atual_pedido, valor_pedido=proximo)


@app.post("/api/truco/aceitar")
def truco_aceitar(request: Request):
    g = request.session.get("truco")
    if not g:
        return JSONResponse({"ok": False, "erro": "Jogo não iniciado."}, status_code=400)
    if g.get("finalizado"):
        return JSONResponse({"ok": False, "erro": "Jogo finalizado."}, status_code=400)

    ped = g.get("pedido_pendente")
    if not ped:
        return JSONResponse({"ok": False, "erro": "Não há pedido pendente."}, status_code=400)

    g["mao_valor"] = int(ped["valor"])
    g["pedido_pendente"] = None
    request.session["truco"] = g

    return JSONResponse({
        "ok": True,
        "acao": "aceitou",
        "mensagem": f"Aceito! Mão valendo {g['mao_valor']}.",
        "placar": [g["placar_user"], g["placar_bot"]],
        "mao_valor": g["mao_valor"],
        "pedido": None,
    })


@app.post("/api/truco/correr")
def truco_correr(request: Request):
    g = request.session.get("truco")
    if not g:
        return JSONResponse({"ok": False, "erro": "Jogo não iniciado."}, status_code=400)
    if g.get("finalizado"):
        return JSONResponse({"ok": False, "erro": "Jogo finalizado."}, status_code=400)

    ped = g.get("pedido_pendente")
    if not ped:
        return JSONResponse({"ok": False, "erro": "Não há pedido pendente."}, status_code=400)

    base = int(ped["base"])
    quem_pediu = ped["por"]  # "user" ou "bot"

    # Quem correu entrega a mão: quem pediu ganha os pontos base
    ganhador = quem_pediu
    res = _aplicar_corrida(request, g, ganhador, base)
    gg = res["g"]

    msg = f"Você correu… {('Você' if ganhador=='user' else 'Bot')} ganhou {base} ponto(s)."

    return JSONResponse({
        "ok": True,
        "acao": "correu",
        "mensagem": msg,
        "nova_mao": res["nova_mao"],
        "fim_jogo": res["fim_jogo"],
        "vira": gg.get("vira"),
        "manilha": gg.get("manilha"),
        "mao_user": gg.get("mao_user"),
        "placar": [gg["placar_user"], gg["placar_bot"]],
        "mao_valor": gg.get("mao_valor", 1),
        "pedido": gg.get("pedido_pendente"),
    })


# =========================
# ✅ JOGAR CARTA
# =========================

@app.post("/api/truco/play")
async def truco_play(request: Request):
    g = request.session.get("truco")
    if not g:
        return JSONResponse({"ok": False, "erro": "Jogo não iniciado."}, status_code=400)
    if g.get("finalizado"):
        return JSONResponse({"ok": False, "erro": "Jogo finalizado."}, status_code=400)
    if g.get("pedido_pendente"):
        return JSONResponse({"ok": False, "erro": "Responda ao pedido (aceitar/correr/aumentar) antes de jogar."}, status_code=400)

    body = await request.json()
    carta_user = body.get("carta")

    if not carta_user or carta_user not in g["mao_user"]:
        return JSONResponse({"ok": False, "erro": "Carta inválida."}, status_code=400)

    carta_bot = random.choice(g["mao_bot"])

    g["mao_user"].remove(carta_user)
    g["mao_bot"].remove(carta_bot)

    g["jogadas_na_mao"] += 1
    jogada_num = g["jogadas_na_mao"]

    r = truco_comparar(carta_user, carta_bot, g["manilha"])

    resultado_rodada = None
    mostrar_maior = None

    # 1ª jogada
    if jogada_num == 1:
        if r == 1:
            g["rodada_user"] += 1
            g["vencedor_rodada1"] = "user"
            resultado_rodada = "venceu"
        elif r == -1:
            g["rodada_bot"] += 1
            g["vencedor_rodada1"] = "bot"
            resultado_rodada = "perdeu"
        else:
            g["empate_rodada1"] = True
            resultado_rodada = "empatou"

            maior_user = truco_maior_da_mao(g["mao_user"], g["manilha"])
            maior_bot = truco_maior_da_mao(g["mao_bot"], g["manilha"])

            if maior_user and maior_bot:
                c = truco_comparar(maior_user, maior_bot, g["manilha"])
                if c == 1:
                    g["vantagem_empate1"] = "user"
                elif c == -1:
                    g["vantagem_empate1"] = "bot"
                else:
                    g["vantagem_empate1"] = None

            mostrar_maior = {
                "user": maior_user,
                "bot": maior_bot,
                "vantagem": g["vantagem_empate1"]
            }

    # 2ª jogada
    elif jogada_num == 2:
        if g["empate_rodada1"] and r != 0:
            if r == 1:
                g["rodada_user"] += 1
                resultado_rodada = "venceu"
            else:
                g["rodada_bot"] += 1
                resultado_rodada = "perdeu"
        else:
            if r == 1:
                g["rodada_user"] += 1
                resultado_rodada = "venceu"
            elif r == -1:
                g["rodada_bot"] += 1
                resultado_rodada = "perdeu"
            else:
                resultado_rodada = "empatou"

    # 3ª jogada
    else:
        if r == 1:
            g["rodada_user"] += 1
            resultado_rodada = "venceu"
        elif r == -1:
            g["rodada_bot"] += 1
            resultado_rodada = "perdeu"
        else:
            resultado_rodada = "empatou"

    # Encerramento da mão
    mao_encerrada = False
    vencedor_mao = None

    if jogada_num == 2 and g["empate_rodada1"] and r != 0:
        mao_encerrada = True
        vencedor_mao = "user" if r == 1 else "bot"

    elif jogada_num == 2 and r == 0:
        if g["vencedor_rodada1"] in ("user", "bot"):
            mao_encerrada = True
            vencedor_mao = g["vencedor_rodada1"]
        elif g["empate_rodada1"] and g["vantagem_empate1"] in ("user", "bot"):
            mao_encerrada = True
            vencedor_mao = g["vantagem_empate1"]

    elif g["rodada_user"] == 2 or g["rodada_bot"] == 2:
        mao_encerrada = True
        vencedor_mao = "user" if g["rodada_user"] == 2 else "bot"

    elif g["jogadas_na_mao"] >= 3:
        mao_encerrada = True
        if g["rodada_user"] > g["rodada_bot"]:
            vencedor_mao = "user"
        elif g["rodada_bot"] > g["rodada_user"]:
            vencedor_mao = "bot"
        else:
            vencedor_mao = None

    nova_mao = False
    fim_jogo = False

    if mao_encerrada:
        valor_mao = int(g.get("mao_valor", 1))

        if vencedor_mao == "user":
            g["placar_user"] += valor_mao
        elif vencedor_mao == "bot":
            g["placar_bot"] += valor_mao

        if g["placar_user"] >= 12 or g["placar_bot"] >= 12:
            g["finalizado"] = True
            fim_jogo = True
            request.session["truco"] = g
        else:
            novo = novo_estado()
            novo["placar_user"] = g["placar_user"]
            novo["placar_bot"] = g["placar_bot"]
            request.session["truco"] = novo
            g = novo
            nova_mao = True

    # Bot pode pedir aumento (às vezes) durante a mão
    if (not fim_jogo) and (not nova_mao) and (not g.get("pedido_pendente")):
        # chance pequena de pedir quando a mão ainda não acabou
        atual = int(g.get("mao_valor", 1))
        nxt = prox_valor(atual)
        if nxt and g.get("jogadas_na_mao", 0) in (1, 2):
            forca = _truco_avaliar_forca_bot(g)
            chance = 0.08 + (forca * 0.16)  # ajuste se quiser
            if random.random() < chance:
                g["pedido_pendente"] = {"por": "bot", "base": atual, "valor": nxt}
                request.session["truco"] = g

    return JSONResponse({
        "ok": True,
        "sua_carta": carta_user,
        "carta_bot": carta_bot,
        "resultado_rodada": resultado_rodada,
        "mostrar_maior": mostrar_maior,

        "vira": g["vira"],
        "manilha": g["manilha"],
        "mao_user": g["mao_user"],
        "placar": [g["placar_user"], g["placar_bot"]],

        "mao_valor": g.get("mao_valor", 1),
        "pedido": g.get("pedido_pendente"),

        "nova_mao": nova_mao,
        "fim_jogo": fim_jogo,
    })
