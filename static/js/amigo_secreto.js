const input = document.getElementById("nome-amigo");
const listaAmigos = document.getElementById("lista-amigos");
const listaSorteio = document.getElementById("lista-sorteio");

const btnAdicionar = document.getElementById("btn-adicionar");
const btnSortear = document.getElementById("btn-sortear");
const btnReiniciar = document.getElementById("btn-reiniciar");

let amigosCache = []; // [{id, name}, ...]

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderAmigos(amigos) {
  amigosCache = amigos || [];

  if (!amigosCache.length) {
    listaAmigos.innerHTML = `<span class="muted">Nenhum até agora</span>`;
    return;
  }

  listaAmigos.innerHTML = amigosCache
    .map(
      (a) => `
      <span class="chip" data-id="${a.id}">
        <span class="chip__name">${escapeHtml(a.name)}</span>
        <button class="chip__btn chip__btn--edit" type="button" title="Editar">Editar</button>
        <button class="chip__btn chip__btn--del" type="button" title="Remover">×</button>
      </span>
    `
    )
    .join("");
}

function renderSorteio(pares) {
  if (!pares || pares.length === 0) {
    listaSorteio.textContent = "Faça o sorteio para ver os pares";
    return;
  }
  listaSorteio.innerHTML = pares.map((p) => `${escapeHtml(p.de)} --> ${escapeHtml(p.para)}`).join("<br>");
}

async function carregarEstado() {
  const resp = await fetch("/api/amigo-secreto/estado");
  const data = await resp.json();
  if (data.ok) renderAmigos(data.amigos);
}

async function adicionar() {
  const nome = input.value.trim();

  try {
    const resp = await fetch("/api/amigo-secreto/adicionar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      alert(data.erro || "Erro ao adicionar.");
      return;
    }

    renderAmigos(data.amigos);
    input.value = "";
    input.focus();
  } catch {
    alert("Falha de conexão com o servidor.");
  }
}

async function remover(friendId) {
  try {
    const resp = await fetch("/api/amigo-secreto/remover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: friendId }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      alert(data.erro || "Erro ao remover.");
      return;
    }

    renderAmigos(data.amigos);
    renderSorteio([]); // limpa sorteio (lista mudou)
  } catch {
    alert("Falha de conexão com o servidor.");
  }
}

async function editar(friendId) {
  const atual = amigosCache.find((a) => a.id === friendId);
  if (!atual) return;

  const novo = prompt("Editar nome:", atual.name);
  if (novo === null) return; // cancelou

  const nome = novo.trim();
  if (!nome) {
    alert("Digite um nome válido.");
    return;
  }

  try {
    const resp = await fetch("/api/amigo-secreto/editar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: friendId, nome }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      alert(data.erro || "Erro ao editar.");
      return;
    }

    renderAmigos(data.amigos);
    renderSorteio([]); // limpa sorteio (lista mudou)
  } catch {
    alert("Falha de conexão com o servidor.");
  }
}

async function sortear() {
  try {
    const resp = await fetch("/api/amigo-secreto/sortear", { method: "POST" });
    const data = await resp.json();

    if (!resp.ok) {
      alert(data.erro || "Erro ao sortear.");
      return;
    }

    renderSorteio(data.pares);
  } catch {
    alert("Falha de conexão com o servidor.");
  }
}

async function reiniciar() {
  try {
    const resp = await fetch("/api/amigo-secreto/reiniciar", { method: "POST" });
    const data = await resp.json();

    if (!resp.ok) {
      alert(data.erro || "Erro ao reiniciar.");
      return;
    }

    renderAmigos([]);
    renderSorteio([]);
    input.value = "";
    input.focus();
  } catch {
    alert("Falha de conexão com o servidor.");
  }
}

btnAdicionar.addEventListener("click", adicionar);
btnSortear.addEventListener("click", sortear);
btnReiniciar.addEventListener("click", reiniciar);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") adicionar();
});

// Delegação de eventos para os chips
listaAmigos.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;

  const id = chip.getAttribute("data-id");
  if (!id) return;

  if (e.target.classList.contains("chip__btn--del")) {
    remover(id);
  } else if (e.target.classList.contains("chip__btn--edit")) {
    editar(id);
  }
});

carregarEstado();
