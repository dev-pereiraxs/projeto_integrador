const lista = document.getElementById("lista");
const pendentesEl = document.getElementById("pendentes");
const andamentoEl = document.getElementById("andamento");
const concluidosEl = document.getElementById("concluidos");

let pedidos = [];
function carregarMeusServicos() {
  fetch('/api/meus_servicos')
    .then(response => response.json())
    .then(data => {
      pedidos = data; // Salva os dados que o Python mandou
      render();       // Desenha na tela
    })
    .catch(erro => {
      console.error("Erro ao buscar os serviços:", erro);
      lista.innerHTML = `<p class="text-center text-red-500 text-sm">Erro ao carregar serviços.</p>`;
    });
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

  pedidos.forEach((p) => {
    const card = document.createElement("div");
    card.className = "card";

    const dataFormatada = p.criado_em ? new Date(p.criado_em).toLocaleDateString('pt-BR') : "Recente";
    const statusServico = p.status || "Publicado";

    card.innerHTML = `
      <div>
        <h3 class="font-semibold">${p.titulo}</h3>
        <p class="text-sm text-gray-500">${dataFormatada}</p>
      </div>

      <div class="flex items-center gap-3">
        <span class="badge ${statusServico.toLowerCase()}">
          ${statusServico}
        </span>

        <button onclick="remover(${p.id})"
          class="text-red-500 text-xs hover:underline">
          excluir
        </button>
      </div>
    `;

    lista.appendChild(card);
  });

  atualizarContadores();
}

// 🔥 2. EXCLUI O SERVIÇO NO BANCO DE DADOS
window.remover = function(id) {
  // Pede uma confirmação antes de apagar do banco
  if (!confirm("Tem certeza que deseja excluir este serviço definitivamente?")) {
    return;
  }

  fetch('/api/excluir_servico/' + id, {
    method: 'DELETE'
  })
  .then(response => response.json())
  .then(data => {
    if (data.erro) {
      alert("Erro: " + data.erro);
    } else {
      carregarMeusServicos();
    }
  })
  .catch(erro => {
    console.error("Erro ao excluir:", erro);
    alert("Ocorreu um erro de conexão ao tentar excluir.");
  });
}

carregarMeusServicos();