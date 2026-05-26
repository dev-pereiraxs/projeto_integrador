document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("lista-servicos");

  if (!container) return;

  if (container.children.length > 0 && !container.querySelector('.sem-servicos')) {
    configurarBotoesAgendar();
    return;
  }

  const CORES_CATEGORIA = {
    tecnologia: { bg: '#EFF6FF', color: '#1D4ED8', emoji: '💻' },
    ti: { bg: '#EFF6FF', color: '#1D4ED8', emoji: '💻' },
    eletrica: { bg: '#FEFCE8', color: '#A16207', emoji: '⚡' },
    elétrica: { bg: '#FEFCE8', color: '#A16207', emoji: '⚡' },
    mecanica: { bg: '#F3F4F6', color: '#374151', emoji: '🔧' },
    mecânica: { bg: '#F3F4F6', color: '#374151', emoji: '🔧' },
    reformas: { bg: '#FFF7ED', color: '#C2410C', emoji: '🛠️' },
    reforma: { bg: '#FFF7ED', color: '#C2410C', emoji: '🛠️' },
    limpeza: { bg: '#F0FDFA', color: '#0F766E', emoji: '🧹' },
    hidraulica: { bg: '#ECFEFF', color: '#0E7490', emoji: '🚰' },
    hidráulica: { bg: '#ECFEFF', color: '#0E7490', emoji: '🚰' },
  };

  function badgeCategoria(categoria) {
    const chave = (categoria || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    const cor = CORES_CATEGORIA[chave] || {
      bg: '#F3F4F6',
      color: '#374151',
      emoji: '🔹'
    };

    return `
      <span style="
        display:inline-flex;
        align-items:center;
        gap:5px;
        background:${cor.bg};
        color:${cor.color};
        font-size:11px;
        font-weight:700;
        letter-spacing:.4px;
        padding:3px 10px;
        border-radius:99px;
        border:1px solid ${cor.color}22;
        text-transform:uppercase;
        margin-bottom:8px;
      ">
        ${cor.emoji} ${categoria || 'Geral'}
      </span>
    `;
  }

  fetch("/api/listar_servicos")
    .then((response) => response.json())
    .then((dados) => {
      container.innerHTML = "";

      if (dados.erro || dados.length === 0) {
        container.innerHTML =
          "<p class='sem-servicos'>Nenhum serviço disponível no momento.</p>";
        return;
      }

      dados.forEach((servico) => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
          <h3>${servico.titulo}</h3>

          ${badgeCategoria(servico.areas_atuacao)}

          <p>${servico.descricao}</p>

          <span class="preco">
            R$ ${servico.preco}
          </span>

          <div class="prestador-nome"
            style="
              margin-top:10px;
              font-size:13px;
              color:var(--text-muted);
              display:flex;
              flex-direction:column;
              gap:4px;
            "
          >
            <div>
              <span class="avaliacao-label">★</span>
              <span class="avaliacao-valor">
                ${servico.avaliacao_media || '—'}
              </span>

              <span>
                — ${servico.nome_prestador}
              </span>
            </div>

            ${servico.telefone ? `
              <div style="
                display:flex;
                align-items:center;
                gap:4px;
                margin-top:2px;
              ">
                <span>📞</span>

                <a
                  href="https://wa.me/55${servico.telefone.replace(/\D/g, '')}"
                  target="_blank"
                  style="
                    color:#2563eb;
                    text-decoration:none;
                    font-weight:600;
                  "
                >
                  ${servico.telefone}
                </a>
              </div>
            ` : ''}
          </div>

          <button
            class="btn-agendar"
            data-servico='${JSON.stringify(servico)}'
          >
            Agendar
          </button>
        `;

        container.appendChild(card);
      });

      configurarBotoesAgendar();
    })
    .catch((erro) => {
      console.error("Erro ao carregar serviços:", erro);

      container.innerHTML = `
        <p class="sem-servicos">
          Erro ao carregar serviços.
        </p>
      `;
    });

  function configurarBotoesAgendar() {
    document.querySelectorAll(".btn-agendar").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();

        try {
          const dataStr = btn.getAttribute("data-servico");

          if (dataStr) {
            const servicoSelecionado = JSON.parse(dataStr);

            localStorage.setItem(
              "servicoSelecionado",
              JSON.stringify(servicoSelecionado)
            );
          }

          window.location.href = "/agendamentos";

        } catch (err) {
          console.error(
            "Erro ao processar clique de agendamento:",
            err
          );

          window.location.href = "/agendamentos";
        }
      });
    });
  }
});