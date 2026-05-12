const lista = document.getElementById("lista");
const pendentesEl = document.getElementById("pendentes");
const andamentoEl = document.getElementById("andamento");
const concluidosEl = document.getElementById("concluidos");

let pedidos = [];

// ============================================================
// CARREGA AGENDAMENTOS DO PRESTADOR
// ============================================================
function carregarMeusServicos() {
  fetch("/api/agendamentos_prestador")
    .then(response => response.json())
    .then(data => {
      if (data.erro) {
        lista.innerHTML = `<p class="estado-erro">${data.erro}</p>`;
        return;
      }
      pedidos = data;
      render();
    })
    .catch(erro => {
      console.error("Erro ao buscar os agendamentos:", erro);
      lista.innerHTML = `<p class="estado-erro">Erro ao carregar agendamentos.</p>`;
    });
}

// ============================================================
// CONTADORES
// ============================================================
function atualizarContadores() {
  let pendentes = 0;
  let andamento = 0;
  let concluidos = 0;

  pedidos.forEach(p => {
    const s = (p.status || "").toLowerCase();
    if (s === "pendente" || s === "confirmado") pendentes++;
    else if (s === "em_andamento") andamento++;
    else if (s === "concluido") concluidos++;
  });

  pendentesEl.textContent = pendentes;
  andamentoEl.textContent = andamento;
  concluidosEl.textContent = concluidos;
}

// ============================================================
// HELPERS DE STATUS
// ============================================================
function statusLabel(s) {
  const mapa = {
    pendente: "Pendente",
    confirmado: "Confirmado",
    em_andamento: "Em andamento",
    concluido: "Concluído",
    cancelado: "Cancelado"
  };
  return mapa[s] || s || "Pendente";
}

function statusClass(s) {
  const mapa = {
    pendente:    "badge-pendente",
    confirmado:  "badge-confirmado",
    em_andamento:"badge-andamento",
    concluido:   "badge-concluido-status",
    cancelado:   "badge-cancelado"
  };
  return mapa[s] || "badge-pendente";
}

// ============================================================
// RENDER
// ============================================================
function render() {
  lista.innerHTML = "";


  if (pedidos.length === 0) {
    lista.innerHTML = `
      <div class="estado-vazio">
        <span class="estado-vazio__icon">📭</span>
        Nenhum agendamento encontrado.
      </div>
    `;
    atualizarContadores();
    return;
  }

  pedidos.forEach((p) => {
    const card = document.createElement("div");
    card.className = "pedido-card";
    card.dataset.agendamentoId = p.id;

    const dataFormatada = p.data_servico
      ? new Date(p.data_servico + "T00:00:00").toLocaleDateString("pt-BR", {
          day: "2-digit", month: "short", year: "numeric"
        })
      : "—";
    const horario = p.horario ? ` às ${p.horario}` : "";
    const meta = `${dataFormatada}${horario}`;

    const cliente = p.cliente_nome
      ? `${p.cliente_nome} ${p.cliente_sobrenome || ""}`.trim()
      : p.cliente_email || "—";

    const status = (p.status || "pendente").toLowerCase();
    const jaConcluido = status === "concluido" || status === "cancelado";

    const badgeHtml = jaConcluido && status === "concluido"
      ? `<span class="badge-concluido">Serviço concluído</span>`
      : `<span class="badge-pill ${statusClass(status)}">${statusLabel(status)}</span>`;

    const btnConcluir = !jaConcluido
      ? `<button
           class="btn-concluir"
           onclick="concluirServicoDireto(${p.id})"
           title="Marcar como concluído"
         >
           ✓ Concluir serviço
         </button>`
      : "";

    card.innerHTML = `
      <div class="pedido-card__info">
        <div class="pedido-card__titulo">${p.servico || "Serviço"}</div>
        <div class="pedido-card__meta">
          <span class="pedido-meta-item">👤 ${cliente}</span>
          <span class="pedido-meta-item">📅 ${meta}</span>
          ${p.observacoes ? `<span class="pedido-meta-item">💬 ${p.observacoes}</span>` : ""}
        </div>
      </div>
      <div class="pedido-card__actions">
        ${badgeHtml}
        ${btnConcluir}
      </div>
    `;

    lista.appendChild(card);
  });

  atualizarContadores();
}

// ============================================================
// REMOVER (mantido para compatibilidade)
// ============================================================
window.remover = function(id) {
  if (!confirm("Tem certeza que deseja excluir este serviço definitivamente?")) return;

  fetch("/api/excluir_servico/" + id, { method: "DELETE" })
    .then(r => r.json())
    .then(data => {
      if (data.erro) { alert("Erro: " + data.erro); return; }
      carregarMeusServicos();
    })
    .catch(() => alert("Ocorreu um erro de conexão ao tentar excluir."));
};

// ============================================================
// INIT
// ============================================================
window.concluirServicoDireto = function (id) {
  fetch(`/api/atualizar_status/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "concluido" })
  })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
      if (!ok || data.erro) {
        alert(data.erro || "Erro ao concluir. Tente novamente.");
        return;
      }
      window.location.href = "/sucesso-conclusao";
    })
    .catch(() => {
      alert("Erro de conexão. Tente novamente.");
    });
};

document.addEventListener("DOMContentLoaded", function () {
  carregarMeusServicos();
});
