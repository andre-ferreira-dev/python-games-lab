const mao = document.getElementById("mao");
const viraSlot = document.getElementById("viraCarta");
const cartaBotSlot = document.getElementById("cartaBot");
const cartaUserSlot = document.getElementById("cartaUser");
const resultado = document.getElementById("resultado");
const pUser = document.getElementById("pUser");
const pBot = document.getElementById("pBot");
const mesaEl = document.getElementById("mesa");

const btnNovo = document.getElementById("btnNovo");
const btnTruco = document.getElementById("btnTruco");
const btnAceitar = document.getElementById("btnAceitar");
const btnCorrer = document.getElementById("btnCorrer");
const maoValorTxt = document.getElementById("maoValorTxt");

const manilhaTxt = document.getElementById("manilhaTxt");
const controle = document.getElementById("controle");

let bloqueado = false;
let timerFimMao = null;
let jogoIniciado = false;

const TEMPO_SUMIR_MAO = 280;
const DELAY_MOSTRAR_USER = 180;
const DELAY_REVELAR_BOT = 420;
const DELAY_TEXTO_PLACAR = 650;
const DELAY_SEGURAR_CARTAS_NA_MESA = 2000;

const ESCADA = [1, 3, 6, 9, 12];

function proxValor(v) {
  const i = ESCADA.indexOf(Number(v));
  return i >= 0 && i < ESCADA.length - 1 ? ESCADA[i + 1] : null;
}

/**
 * Pré-jogo: controle centralizado.
 * Jogo rodando: controle no canto inferior direito.
 */
function setModoJogo(rodando) {
  if (!mesaEl) return;
  mesaEl.classList.toggle("pre-game", !rodando);
}

let estado = {
  mao_valor: 1,
  pedido: null,
  manilha: null,
  vez: "user",
};

function renderCarta(slot, carta) {
  slot.innerHTML = `<img src="/img/img-truco/${carta}.png" alt="${carta}">`;
}

function limparMesa() {
  cartaBotSlot.innerHTML = "";
  cartaUserSlot.innerHTML = "";
}

function setPlacar(arr) {
  pUser.textContent = arr[0];
  pBot.textContent = arr[1];
}

function renderMao(cartas) {
  mao.innerHTML = "";
  cartas.forEach((carta) => {
    const botao = document.createElement("button");
    botao.className = "card";
    botao.type = "button";
    botao.innerHTML = `<img src="/img/img-truco/${carta}.png" alt="${carta}">`;
    botao.onclick = () => jogarCarta(botao, carta);
    mao.appendChild(botao);
  });
}

function setMaoDisabled(disabled) {
  [...mao.querySelectorAll("button.card")].forEach((btn) => {
    btn.disabled = disabled;
  });
}

function cancelarTimerFimMao() {
  if (timerFimMao) {
    clearTimeout(timerFimMao);
    timerFimMao = null;
  }
}

function setEstadoTruco(d) {
  estado.mao_valor = d.mao_valor ?? estado.mao_valor;
  estado.pedido = d.pedido ?? null;
  estado.manilha = d.manilha ?? estado.manilha;
  estado.vez = d.vez ?? estado.vez;

  maoValorTxt.textContent = `Mão valendo ${estado.mao_valor}`;
  manilhaTxt.textContent = `Manilha: ${estado.manilha || "-"}`;

  const deveTravar = !!estado.pedido || estado.vez !== "user";
  controle.classList.toggle("pedido", !!estado.pedido);
  setMaoDisabled(deveTravar);

  atualizarBotoes();
}

function atualizarBotoes() {
  if (!jogoIniciado) {
    btnTruco.style.display = "none";
    btnAceitar.style.display = "none";
    btnCorrer.style.display = "none";
    return;
  }

  const ped = estado.pedido;

  if (ped) {
    btnAceitar.style.display = "inline-block";
    btnCorrer.style.display = "inline-block";

    if (ped.por === "bot") {
      const proximo = proxValor(ped.valor);
      btnTruco.style.display = "inline-block";
      btnTruco.textContent = proximo ? `Aumentar pra ${proximo}` : "Aumentar";
      btnTruco.disabled = !proximo;
    } else {
      btnTruco.style.display = "none";
    }
    return;
  }

  btnAceitar.style.display = "none";
  btnCorrer.style.display = "none";

  const proximo = proxValor(estado.mao_valor);
  btnTruco.style.display = "inline-block";
  btnTruco.textContent = proximo ? `Pedir ${proximo}` : "Máximo";
  btnTruco.disabled = !proximo;
}

function mostrarBotTornou(carta) {
  if (!carta) return;

  // ✅ limpa as cartas da rodada anterior (principalmente a sua carta)
  limparMesa();

  // ✅ agora mostra a carta que o bot tornou
  cartaBotSlot.innerHTML = `<img src="/img/img-truco/${carta}.png" alt="${carta}">`;
  resultado.textContent = "Bot tornou — responda com uma carta";
}

async function novoJogo() {
  if (bloqueado) return;

  cancelarTimerFimMao();
  bloqueado = true;
  btnNovo.disabled = true;

  try {
    mao.innerHTML = "";
    limparMesa();
    resultado.textContent = "Distribuindo cartas...";

    const r = await fetch("/api/truco/new");
    const d = await r.json();

    if (!r.ok || !d.ok) {
      resultado.textContent = d?.erro || "Falha ao iniciar novo jogo.";
      jogoIniciado = false;
      setModoJogo(false);
      atualizarBotoes();
      bloqueado = false;
      btnNovo.disabled = false;
      return;
    }

    renderCarta(viraSlot, d.vira);
    setPlacar(d.placar);
    renderMao(d.mao_user);

    jogoIniciado = true;
    setModoJogo(true);
    setEstadoTruco(d);

    resultado.textContent = estado.vez === "user" ? "Escolha uma carta" : "Aguarde o bot jogar...";
  } catch (err) {
    console.error(err);
    jogoIniciado = false;
    setModoJogo(false);
    atualizarBotoes();
    resultado.textContent = "Erro ao iniciar o jogo. Tente novamente.";
  } finally {
    bloqueado = false;
    btnNovo.disabled = false;
  }
}

async function pedirOuAumentar() {
  if (bloqueado) return;

  cancelarTimerFimMao();
  bloqueado = true;

  try {
    // Se bot pediu, o botão vira "Aumentar"
    if (estado.pedido && estado.pedido.por === "bot") {
      const r = await fetch("/api/truco/aumentar", { method: "POST" });
      const d = await r.json();

      if (!r.ok || !d.ok) {
        resultado.textContent = d?.erro || "Falha ao aumentar.";
        bloqueado = false;
        return;
      }

      if (d.mensagem) resultado.textContent = d.mensagem;

      if (d.nova_mao) {
        limparMesa();
        renderCarta(viraSlot, d.vira);
        renderMao(d.mao_user);
        setModoJogo(true);
      }

      setPlacar(d.placar);
      setEstadoTruco(d);

      if (d.bot_iniciou) mostrarBotTornou(d.bot_iniciou);

      if (d.fim_jogo) {
        const u = Number(d.placar[0]);
        const b = Number(d.placar[1]);
        resultado.textContent = u > b ? "FIM DE JOGO — Você venceu! 🏆" : "FIM DE JOGO — Bot venceu!";
        bloqueado = true;
        return;
      }

      bloqueado = false;
      return;
    }

    // Pedido normal (user)
    if (estado.vez !== "user") {
      resultado.textContent = "Você só pode pedir truco na sua vez.";
      bloqueado = false;
      return;
    }

    const r = await fetch("/api/truco/pedir", { method: "POST" });
    const d = await r.json();

    if (!r.ok || !d.ok) {
      resultado.textContent = d?.erro || "Falha ao pedir.";
      bloqueado = false;
      return;
    }

    if (d.mensagem) resultado.textContent = d.mensagem;

    if (d.nova_mao) {
      limparMesa();
      renderCarta(viraSlot, d.vira);
      renderMao(d.mao_user);
      setModoJogo(true);
    }

    setPlacar(d.placar);
    setEstadoTruco(d);

    if (d.bot_iniciou) mostrarBotTornou(d.bot_iniciou);

    if (d.fim_jogo) {
      const u = Number(d.placar[0]);
      const b = Number(d.placar[1]);
      resultado.textContent = u > b ? "FIM DE JOGO — Você venceu! 🏆" : "FIM DE JOGO — Bot venceu!";
      bloqueado = true;
      return;
    }

    bloqueado = false;
  } catch (err) {
    console.error(err);
    resultado.textContent = "Erro ao pedir/aumentar.";
    bloqueado = false;
  }
}

async function aceitarPedido() {
  if (bloqueado) return;

  cancelarTimerFimMao();
  bloqueado = true;

  try {
    const r = await fetch("/api/truco/aceitar", { method: "POST" });
    const d = await r.json();

    if (!r.ok || !d.ok) {
      resultado.textContent = d?.erro || "Erro ao aceitar.";
      bloqueado = false;
      return;
    }

    if (d.mensagem) resultado.textContent = d.mensagem;
    setPlacar(d.placar);
    setEstadoTruco(d);

    if (d.bot_iniciou) mostrarBotTornou(d.bot_iniciou);
    else resultado.textContent = estado.vez === "user" ? "Escolha uma carta" : "Aguarde o bot jogar...";

    bloqueado = false;
  } catch (err) {
    console.error(err);
    resultado.textContent = "Erro ao aceitar.";
    bloqueado = false;
  }
}

async function correrPedido() {
  if (bloqueado) return;

  cancelarTimerFimMao();
  bloqueado = true;

  try {
    const r = await fetch("/api/truco/correr", { method: "POST" });
    const d = await r.json();

    if (!r.ok || !d.ok) {
      resultado.textContent = d?.erro || "Erro ao correr.";
      bloqueado = false;
      return;
    }

    if (d.mensagem) resultado.textContent = d.mensagem;

    if (d.nova_mao) {
      limparMesa();
      renderCarta(viraSlot, d.vira);
      renderMao(d.mao_user);
      setModoJogo(true);
    }

    setPlacar(d.placar);
    setEstadoTruco(d);

    if (d.bot_iniciou) mostrarBotTornou(d.bot_iniciou);

    if (d.fim_jogo) {
      const u = Number(d.placar[0]);
      const b = Number(d.placar[1]);
      resultado.textContent = u > b ? "FIM DE JOGO — Você venceu! 🏆" : "FIM DE JOGO — Bot venceu!";
      bloqueado = true;
      return;
    }

    bloqueado = false;
  } catch (err) {
    console.error(err);
    resultado.textContent = "Erro ao correr.";
    bloqueado = false;
  }
}

async function jogarCarta(botao, carta) {
  if (bloqueado) return;

  if (estado.pedido) {
    resultado.textContent = "Responda ao pedido (Aceitar/Correr/Aumentar) antes de jogar.";
    return;
  }

  if (estado.vez !== "user") {
    resultado.textContent = "Aguarde o bot jogar...";
    return;
  }

  cancelarTimerFimMao();
  bloqueado = true;

  botao.classList.add("jogada");
  setTimeout(() => botao.remove(), TEMPO_SUMIR_MAO);

  setTimeout(() => {
    cartaUserSlot.innerHTML = `<img src="/img/img-truco/${carta}.png" alt="${carta}">`;
  }, DELAY_MOSTRAR_USER);

  cartaBotSlot.innerHTML = `<img src="/img/img-truco/back.png" alt="back">`;

  try {
    const r = await fetch("/api/truco/play", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ carta }),
    });

    const d = await r.json();

    if (!r.ok) {
      resultado.textContent = d?.erro || "Falha ao jogar carta.";
      bloqueado = false;
      return;
    }

    setEstadoTruco(d);

    setTimeout(() => {
      cartaBotSlot.innerHTML = `<img src="/img/img-truco/${d.carta_bot}.png" alt="${d.carta_bot}">`;
    }, DELAY_REVELAR_BOT);

    setTimeout(() => {
      setPlacar(d.placar);

      if (d.resultado_rodada === "empatou") resultado.textContent = "Rodada empatada";
      else resultado.textContent = `Você ${d.resultado_rodada} a rodada`;

      if (d.pedido && d.pedido.por === "bot") {
        resultado.textContent = `Bot pediu ${d.pedido.valor}! Aceita, corre ou aumenta?`;
      }
    }, DELAY_TEXTO_PLACAR);

    timerFimMao = setTimeout(() => {
      if (d.fim_jogo) {
        const u = Number(d.placar[0]);
        const b = Number(d.placar[1]);
        resultado.textContent = u > b ? "FIM DE JOGO — Você venceu! 🏆" : "FIM DE JOGO — Bot venceu!";
        bloqueado = true;
        return;
      }

      if (d.nova_mao) {
        resultado.textContent = "Nova mão! Escolha uma carta";
        limparMesa();
        renderCarta(viraSlot, d.vira);
        renderMao(d.mao_user);
        jogoIniciado = true;
        setModoJogo(true);
        atualizarBotoes();
        bloqueado = false;
        return;
      }

      // ✅ Se o bot tornou automaticamente, a carta vem em bot_iniciou
      if (d.bot_iniciou) {
        mostrarBotTornou(d.bot_iniciou);
        bloqueado = false;
        return;
      }

      if (mao.children.length > 0) {
        if (estado.pedido) {
          resultado.textContent = `Bot pediu ${estado.pedido.valor}! Aceita, corre ou aumenta?`;
          bloqueado = false;
          return;
        }

        resultado.textContent = estado.vez === "user" ? "Escolha uma carta" : "Aguarde o bot jogar...";
        bloqueado = false;
      } else {
        resultado.textContent = "Clique em “Novo jogo”";
        jogoIniciado = false;
        setModoJogo(false);
        atualizarBotoes();
        bloqueado = false;
      }
    }, DELAY_SEGURAR_CARTAS_NA_MESA);
  } catch (err) {
    console.error(err);
    resultado.textContent = "Erro ao jogar. Clique em “Novo jogo”.";
    jogoIniciado = false;
    setModoJogo(false);
    atualizarBotoes();
    bloqueado = false;
  }
}

btnNovo.addEventListener("click", novoJogo);
btnTruco.addEventListener("click", pedirOuAumentar);
btnAceitar.addEventListener("click", aceitarPedido);
btnCorrer.addEventListener("click", correrPedido);

// Estado inicial: pré-jogo (controle central)
setModoJogo(false);
atualizarBotoes();