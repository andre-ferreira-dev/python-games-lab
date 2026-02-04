const input = document.getElementById("nome-amigo");
const listaAmigos = document.getElementById("lista-amigos");
const listaSorteio = document.getElementById("lista-sorteio");

const btnAdicionar = document.getElementById("btn-adicionar");
const btnSortear = document.getElementById("btn-sortear");
const btnReiniciar = document.getElementById("btn-reiniciar");

// ===== Modal Editar (custom) =====
const editModal = document.getElementById("edit-modal");
const editInput = document.getElementById("edit-input");
const editCancel = document.getElementById("edit-cancel");
const editSave = document.getElementById("edit-save");

let editId = null;

function openEditModal(id, currentName) {
  editId = id;

  editModal.classList.add("is-open");
  editModal.setAttribute("aria-hidden", "false");

  editInput.value = currentName || "";
  setTimeout(() => {
    editInput.focus();
    editInput.select();
  }, 0);
}

function closeEditModal() {
  editModal.classList.remove("is-open");
  editModal.setAttribute("aria-hidden", "true");
  editId = null;
}

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

        <span class="chip__actions">
          <button class="chip__btn chip__btn--edit" type="button" title="Editar" aria-label="Editar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 17.25V21h3.75L17.8 9.95l-3.75-3.75L3 17.25Z" fill="currentColor"/>
              <path d="M20.7 7.04c.39-.39.39-1.02 0-1.41L18.37 3.3a.9959.9959 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.82-1.84Z" fill="currentColor"/>
            </svg>
          </button>

          <button class="chip__btn chip__btn--del" type="button" title="Remover" aria-label="Remover">×</button>
        </span>
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
  listaSorteio.innerHTML = pares
    .map((p) => `${escapeHtml(p.de)} → ${escapeHtml(p.para)}`)
    .join("<br>");
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
    renderSorteio([]); // opcional: limpa sorteio quando lista muda
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

// Agora: abre modal (não usa prompt)
function editar(friendId) {
  const atual = amigosCache.find((a) => a.id === friendId);
  if (!atual) return;
  openEditModal(friendId, atual.name);
}

// Salva a edição do modal
async function salvarEdicao() {
  if (!editId) return;

  const nome = editInput.value.trim();
  if (!nome) {
    alert("Digite um nome válido.");
    editInput.focus();
    return;
  }

  try {
    const resp = await fetch("/api/amigo-secreto/editar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: editId, nome }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      alert(data.erro || "Erro ao editar.");
      return;
    }

    renderAmigos(data.amigos);
    renderSorteio([]); // limpa sorteio (lista mudou)
    closeEditModal();
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

// ===== Eventos principais =====
btnAdicionar.addEventListener("click", adicionar);
btnSortear.addEventListener("click", sortear);
btnReiniciar.addEventListener("click", reiniciar);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") adicionar();
});

// Delegação de eventos para chips (edit/del funciona com SVG)
listaAmigos.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;

  const id = chip.getAttribute("data-id");
  if (!id) return;

  if (e.target.closest(".chip__btn--del")) {
    remover(id);
    return;
  }

  if (e.target.closest(".chip__btn--edit")) {
    editar(id);
    return;
  }
});

// ===== Eventos do Modal =====
editCancel.addEventListener("click", closeEditModal);
editSave.addEventListener("click", salvarEdicao);

// Fechar clicando fora (overlay tem data-close="true")
editModal.addEventListener("click", (e) => {
  if (e.target.dataset.close === "true") closeEditModal();
});

// Enter salva / Esc fecha (apenas quando modal aberto)
document.addEventListener("keydown", (e) => {
  if (!editModal.classList.contains("is-open")) return;

  if (e.key === "Escape") closeEditModal();
  if (e.key === "Enter") salvarEdicao();
});

carregarEstado();
