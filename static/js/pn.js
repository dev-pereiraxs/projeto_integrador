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
    cancelado: "Cancelado",
    recusado: "Recusado"
  };
  return mapa[s] || s || "Pendente";
}

function statusClass(s) {
  const mapa = {
    pendente: "badge-pendente",
    confirmado: "badge-confirmado",
    em_andamento: "badge-andamento",
    concluido: "badge-concluido-status",
    cancelado: "badge-cancelado",
    recusado: "badge-cancelado"
  };
  return mapa[s] || "badge-pendente";
}

// ============================================================
// RENDER (Com Ordenação Automática e Botões Premium)
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

  // LÓGICA DE ORDENAÇÃO INTELIGENTE DOS CARDS
  const ordemStatus = {
    "pendente": 1,
    "confirmado": 2,
    "em_andamento": 2,
    "concluido": 3,
    "cancelado": 4,
    "recusado": 4
  };

  pedidos.sort((a, b) => {
    const statusA = (a.status || "pendente").toLowerCase();
    const statusB = (b.status || "pendente").toLowerCase();
    const pesoA = ordemStatus[statusA] || 99;
    const pesoB = ordemStatus[statusB] || 99;

    if (pesoA !== pesoB) return pesoA - pesoB;
    return b.id - a.id;
  });

  // MONTAGEM DOS CARDS
  pedidos.forEach((p) => {
    const card = document.createElement("div");
    card.className = "pedido-card";

    const status = (p.status || "pendente").toLowerCase();
    card.setAttribute("data-status", status);
    card.dataset.agendamentoId = p.id;

    let dataFormatada = "—";
    if (p.data_servico) {
      const parsedDate = new Date(p.data_servico);
      if (!isNaN(parsedDate.getTime())) {
        dataFormatada = parsedDate.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
      } else {
        dataFormatada = p.data_servico.split("T")[0] || p.data_servico;
      }
    }

    const horario = p.horario ? ` às ${p.horario}` : "";
    const meta = `${dataFormatada}${horario}`;

    const cliente = p.cliente_nome
      ? `${p.cliente_nome} ${p.cliente_sobrenome || ""}`.trim()
      : p.cliente_email || "—";

    const jaConcluido = status === "concluido" || status === "cancelado" || status === "recusado";
    const badgeHtml = `<span class="badge-pill ${statusClass(status)}">${statusLabel(status)}</span>`;

    let botoesAcao = "";

    if (status === "pendente") {
      botoesAcao = `
        <button class="btn btn-action" onclick="alterarStatus(${p.id}, 'confirmado')" style="color: #059669; border: #a7f3d0 1px solid; border-radius: 8px; padding: 6px 14px; font-weight: 700; font-size: 13px; cursor: pointer; background: #ecfdf5; transition: opacity 0.2s;">
          ✓ Aceitar
        </button>
        <button class="btn btn-action" onclick="abrirModalRecusar(${p.id})" style="color: #dc2626; border: #fecaca 1px solid; border-radius: 8px; padding: 6px 14px; font-weight: 700; font-size: 13px; cursor: pointer; background: #fef2f2; transition: opacity 0.2s;">
          ✕ Recusar
        </button>
      `;
    } else if (!jaConcluido) {
      botoesAcao = `
        <button onclick="abrirModalConcluir(${p.id})" title="Marcar como concluído" style="color: #ffffff; background: #10b981; border: none; border-radius: 8px; padding: 6px 14px; font-size: 13px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25); margin-left: auto; transition: transform 0.15s, opacity 0.2s;">
          ✓ Concluir
        </button>
      `;
    }

    card.innerHTML = `
      <div class="pedido-card__info">
        <div class="pedido-card__titulo">${p.servico || "Serviço"}</div>
        <div class="pedido-card__meta">
          <span class="pedido-meta-item">👤 <strong>Cliente:</strong> ${cliente}</span>
          <span class="pedido-meta-item">📅 <strong>Data:</strong> ${meta}</span>
          ${p.observacoes ? `<span class="pedido-meta-item">💬 <strong>Obs:</strong> ${p.observacoes}</span>` : ""}
        </div>
      </div>
      <div class="pedido-card__actions" style="display: flex; gap: 8px; align-items: center; justify-content: space-between; width: 100%;">
        ${badgeHtml}
        <div style="display: flex; gap: 8px; align-items: center;">
          ${botoesAcao}
        </div>
      </div>
    `;

    lista.appendChild(card);
  });

  atualizarContadores();
}

// ============================================================
// FUNÇÃO GENÉRICA DE ATUALIZAR STATUS (Aceitar)
// ============================================================
window.alterarStatus = function(id, novoStatus) {
  fetch(`/api/atualizar_status/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: novoStatus })
  })
  .then(res => res.json())
  .then(data => {
    if (data.erro) {
      alert("Erro ao atualizar: " + data.erro);
      return;
    }
    carregarMeusServicos();
  })
  .catch(() => alert("Erro de conexão com o servidor."));
};

// ============================================================
// CONTROLE DOS MODAIS (RECUSAR E CONCLUIR)
// ============================================================
let idAgendamentoParaRecusar = null;
let idAgendamentoParaConcluir = null;

window.abrirModalRecusar = function(id) {
  idAgendamentoParaRecusar = id;
  const modal = document.getElementById('modalRecusar');
  if (modal) modal.classList.add('open');
};

window.fecharModalRecusar = function() {
  idAgendamentoParaRecusar = null;
  const modal = document.getElementById('modalRecusar');
  if (modal) modal.classList.remove('open');
};

window.abrirModalConcluir = function(id) {
  idAgendamentoParaConcluir = id;
  const modal = document.getElementById('modalConcluir');
  if (modal) modal.classList.add('open');
};

window.fecharModalConcluir = function() {
  idAgendamentoParaConcluir = null;
  const modal = document.getElementById('modalConcluir');
  if (modal) modal.classList.remove('open');
};

// ============================================================
// EVENTOS PRINCIPAIS
// ============================================================
document.addEventListener("DOMContentLoaded", function () {
  const btnPedidos = document.getElementById("btn-pedidos");
  const btnServicos = document.getElementById("btn-servicos");

  // FECHAR MODAIS CLICANDO FORA
  const modalRec = document.getElementById('modalRecusar');
  if (modalRec) modalRec.addEventListener('click', function(e) { if (e.target === this) fecharModalRecusar(); });

  const modalConc = document.getElementById('modalConcluir');
  if (modalConc) modalConc.addEventListener('click', function(e) { if (e.target === this) fecharModalConcluir(); });

  // CONFIRMAR RECUSA
  const btnConfirmarRecusa = document.getElementById('btnConfirmarRecusa');
  if (btnConfirmarRecusa) {
    btnConfirmarRecusa.addEventListener('click', async function() {
      if (!idAgendamentoParaRecusar) return;
      const btn = this;
      const textoOriginal = btn.textContent;
      btn.textContent = 'Aguarde...';
      btn.disabled = true;
      btn.style.opacity = '0.7';

      try {
        const res = await fetch(`/api/atualizar_status/${idAgendamentoParaRecusar}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "recusado" })
        });

        const data = await res.json();
        if (data.erro) {
          alert("Erro no servidor: " + data.erro);
        } else {
          fecharModalRecusar();
          carregarMeusServicos();
        }
      } catch (e) {
        alert('Erro de conexão.');
      } finally {
        btn.textContent = textoOriginal;
        btn.disabled = false;
        btn.style.opacity = '1';
      }
    });
  }

  // CONFIRMAR CONCLUSÃO
  const btnConfirmarConclusao = document.getElementById('btnConfirmarConclusao');
  if (btnConfirmarConclusao) {
    btnConfirmarConclusao.addEventListener('click', async function() {
      if (!idAgendamentoParaConcluir) return;
      const btn = this;
      const textoOriginal = btn.textContent;
      btn.textContent = 'Concluindo...';
      btn.disabled = true;
      btn.style.opacity = '0.7';

      try {
        const res = await fetch(`/api/atualizar_status/${idAgendamentoParaConcluir}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "concluido" })
        });
        const data = await res.json();

        if (data.erro) {
          alert(data.erro);
        } else {
          window.location.href = "/sucesso-conclusao";
        }
      } catch (e) {
        alert('Erro de conexão.');
      } finally {
        btn.textContent = textoOriginal;
        btn.disabled = false;
        btn.style.opacity = '1';
        fecharModalConcluir();
      }
    });
  }

  // ABAS
  function setAba(aba) {
    btnPedidos.classList.toggle("btn-aba-ativo", aba === "pedidos");
    btnServicos.classList.toggle("btn-aba-ativo", aba === "servicos");
    if (aba === "pedidos") carregarMeusServicos();
    else carregarServicos();
  }

  btnPedidos.addEventListener("click", () => setAba("pedidos"));
  btnServicos.addEventListener("click", () => setAba("servicos"));

  setAba("pedidos");
});

// ============================================================
// ABA: MEUS SERVIÇOS (Design Premium Automático e Remover)
// ============================================================
window.remover = function (id) {
  if (!confirm("Tem certeza que deseja excluir este serviço?")) return;
  fetch("/api/excluir_servico/" + id, { method: "DELETE" })
    .then(r => r.json())
    .then(data => {
      if (data.erro) { alert("Erro: " + data.erro); return; }
      carregarServicos(); // Atualiza a aba serviços após excluir
    }).catch(() => alert("Erro ao excluir."));
};

function carregarServicos() {
  fetch("/api/meus_servicos")
    .then(r => r.json())
    .then(data => {
      if (data.erro) {
        lista.innerHTML = `<p class="estado-erro">${data.erro}</p>`;
        return;
      }
      if (data.length === 0) {
        lista.innerHTML = `
          <div class="estado-vazio">
            <span class="estado-vazio__icon">🛠️</span>
            Nenhum serviço cadastrado.
          </div>`;
        return;
      }

      lista.innerHTML = "";

      // Dicionário de Ícones e Cores por Área de Atuação
      const categorias = {
        "tecnologia": { icon: "💻", color: "#3b82f6", bg: "#eff6ff" },
        "mecanica":   { icon: "⚙️", color: "#64748b", bg: "#f8fafc" },
        "eletrica":   { icon: "⚡", color: "#eab308", bg: "#fefce8" },
        "hidraulica": { icon: "💧", color: "#0ea5e9", bg: "#f0f9ff" },
        "reformas":   { icon: "🏗️", color: "#f97316", bg: "#fff7ed" },
        "limpeza":    { icon: "🧹", color: "#10b981", bg: "#ecfdf5" }
      };

      data.forEach(s => {
        const card = document.createElement("div");
        card.className = "pedido-card";

        const area = (s.area_atuacao || "").toLowerCase();
        const config = categorias[area] || { icon: "📌", color: "#8b5cf6", bg: "#f5f3ff" };

        const precoMoeda = Number(s.preco).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        card.innerHTML = `
          <div style="display: flex; gap: 20px; align-items: center; width: 100%; flex-wrap: wrap;">
            
            <div style="width: 64px; height: 64px; border-radius: 18px; background-color: ${config.bg}; color: ${config.color}; display: flex; align-items: center; justify-content: center; font-size: 32px; flex-shrink: 0; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
              ${config.icon}
            </div>

            <div style="flex: 1; min-width: 200px;">
              <div class="pedido-card__titulo" style="margin-bottom: 8px; font-size: 18px;">${s.titulo}</div>
              
              <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                <span style="color: #10b981; font-weight: 800; font-size: 15px; background: #ecfdf5; padding: 4px 12px; border-radius: 8px; display: inline-flex; align-items: center; gap: 4px;">
                  💰 R$ ${precoMoeda}
                </span>
                
                <span style="color: #64748b; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; text-transform: capitalize; background: #f1f5f9; padding: 4px 12px; border-radius: 8px;">
                  <span style="display: block; width: 8px; height: 8px; border-radius: 50%; background-color: ${config.color};"></span>
                  ${s.area_atuacao || "Serviços Gerais"}
                </span>
              </div>
            </div>

            <div style="flex-shrink: 0; margin-left: auto;">
              <button onclick="remover(${s.id})" style="display: flex; align-items: center; gap: 8px; padding: 12px 20px; border: 1px solid #fecaca; border-radius: 12px; background-color: #fef2f2; color: #ef4444; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.backgroundColor='#fee2e2'; this.style.transform='translateY(-2px)';" onmouseout="this.style.backgroundColor='#fef2f2'; this.style.transform='translateY(0)';">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Excluir
              </button>
            </div>

          </div>
        `;
        lista.appendChild(card);
      });
    })
    .catch(() => {
      lista.innerHTML = `<p class="estado-erro">Erro ao carregar serviços.</p>`;
    });
}