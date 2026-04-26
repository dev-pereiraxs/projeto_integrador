const lista = document.getElementById("lista");

const pendentesEl = document.getElementById("pendentes");
const andamentoEl = document.getElementById("andamento");
const concluidosEl = document.getElementById("concluidos");


let pedidos = JSON.parse(localStorage.getItem("servicos"));

if (!pedidos) {
  pedidos = [];
  localStorage.setItem("servicos", JSON.stringify(pedidos));
}


function atualizarContadores() {
  let pendentes = 0;
  let andamento = 0;
  let concluidos = 0;

  pedidos.forEach(p => {
    if (p.status === "pendente") pendentes++;
    else if (p.status === "andamento") andamento++;
    else if (p.status === "concluido") concluidos++;
  });

  pendentesEl.textContent = pendentes;
  andamentoEl.textContent = andamento;
  concluidosEl.textContent = concluidos;
}


function render() {
  lista.innerHTML = "";

  if (pedidos.length === 0) {
    lista.innerHTML = `
      <p class="text-center text-gray-400 text-sm">
        Nenhum serviço cadastrado
      </p>
    `;
    atualizarContadores();
    return;
  }

  pedidos.forEach((p, index) => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <div>
        <h3 class="font-semibold">${p.titulo}</h3>
        <p class="text-sm text-gray-500">${p.data}</p>
      </div>

      <div class="flex items-center gap-3">
        <span class="badge ${p.status}">
          ${p.status}
        </span>

        <!-- botão excluir -->
        <button onclick="remover(${index})"
          class="text-red-500 text-xs hover:underline">
          excluir
        </button>
      </div>
    `;

    lista.appendChild(card);
  });

  atualizarContadores();
}


function remover(index) {
  pedidos.splice(index, 1);
  localStorage.setItem("servicos", JSON.stringify(pedidos));
  render();
}


render();
