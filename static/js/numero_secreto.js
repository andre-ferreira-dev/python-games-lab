const input = document.querySelector(".container__input");
const h1 = document.querySelector("h1");
const p = document.querySelector(".texto__paragrafo");

const btnChutar = document.getElementById("btnChutar");
const btnReiniciar = document.getElementById("reiniciar");

function setTexto(titulo, mensagem) {
  if (titulo) h1.innerHTML = titulo;
  p.innerHTML = mensagem;
}

function limparCampo() {
  input.value = "";
  input.focus();
}

async function chutar() {
  const chute = input.value;

  try {
    const resp = await fetch("/api/numero-secreto/chute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chute }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      setTexto(null, data.erro || "Erro ao processar o chute.");
      return;
    }

    if (data.titulo) setTexto(data.titulo, data.mensagem);
    else setTexto(null, data.mensagem);

    btnReiniciar.disabled = !data.reiniciar_habilitado;

    if (data.acertou) {
      btnChutar.disabled = true;
    } else {
      limparCampo();
    }
  } catch {
    setTexto(null, "Falha de conexão com o servidor.");
  }
}

async function novoJogo() {
  try {
    const resp = await fetch("/api/numero-secreto/novo-jogo", { method: "POST" });
    const data = await resp.json();

    setTexto(data.titulo, data.mensagem);
    btnReiniciar.disabled = true;
    btnChutar.disabled = false;
    limparCampo();
  } catch {
    setTexto(null, "Falha ao iniciar novo jogo.");
  }
}

btnChutar.addEventListener("click", chutar);
btnReiniciar.addEventListener("click", novoJogo);

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") chutar();
});

// Estado inicial da tela
setTexto("Jogo do número secreto", "Escolha um número entre 1 e 100");
limparCampo();
