const btnSortear = document.getElementById("btn-sortear");
const btnReiniciar = document.getElementById("btn-reiniciar");

function setResultado(texto) {
  document.getElementById("resultado").innerHTML =
    `<label class="texto__paragrafo">${texto}</label>`;
}

function habilitarReiniciar(habilitar) {
  btnReiniciar.disabled = !habilitar;

  if (habilitar) {
    btnReiniciar.classList.remove("container__botao-desabilitado");
    btnReiniciar.classList.add("container__botao");
  } else {
    btnReiniciar.classList.remove("container__botao");
    btnReiniciar.classList.add("container__botao-desabilitado");
  }
}

async function sortear() {
  const quantidade = document.getElementById("quantidade").value;
  const de = document.getElementById("de").value;
  const ate = document.getElementById("ate").value;

  try {
    const resp = await fetch("/api/sorteador/sortear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quantidade, de, ate }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      alert(data.erro || "Erro ao sortear.");
      return;
    }

    setResultado(`Números sorteados: ${data.sorteados.join(", ")}`);
    habilitarReiniciar(true);

  } catch (e) {
    alert("Falha de conexão com o servidor.");
  }
}

function reiniciar() {
  document.getElementById("quantidade").value = "";
  document.getElementById("de").value = "";
  document.getElementById("ate").value = "";
  setResultado("Números sorteados: nenhum até agora");
  habilitarReiniciar(false);
}

btnSortear.addEventListener("click", sortear);
btnReiniciar.addEventListener("click", reiniciar);

// Inicia com reiniciar desabilitado
habilitarReiniciar(false);
