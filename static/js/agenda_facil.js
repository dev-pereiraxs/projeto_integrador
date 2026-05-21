document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("lista-servicos"); // Ajustado para o ID real do seu HTML

  if (!container) return;

  // Se o container já tiver cards renderizados pelo Python, não faz nada para não duplicar,
  // a menos que queira recarregar os dados dinamicamente.
  if (container.children.length > 0 && !container.querySelector('.sem-servicos')) {
      // Configura apenas o clique dos botões que vieram do Python
      configurarBotoesAgendar();
      return;
  }

  fetch("/api/listar_servicos")
    .then((response) => response.json())
    .then((dados) => {
      container.innerHTML = "";

      if (dados.erro || dados.length === 0) {
        container.innerHTML = "<p class='sem-servicos'>Nenhum serviço disponível no momento.</p>";
        return;
      }

      dados.forEach((servico) => {
        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
          <h3>${servico.titulo}</h3>
          <p>${servico.descricao}</p>
          <span class="preco">R$ ${servico.preco}</span>
          
          <div class="prestador-nome" style="margin-top: 10px; font-size: 13px; color: var(--text-muted); display: flex; flex-direction: column; gap: 4px;">
            <div>
              <span class="avaliacao-label">★</span>
              <span class="avaliacao-valor">${servico.avaliacao_media || '—'}</span>
              <span> — ${servico.nome_prestador}</span>
            </div>
            ${servico.telefone ? `
            <div style="display: flex; align-items: center; gap: 4px; margin-top: 2px;">
              <span>📞</span>
              <a href="https://wa.me/55${servico.telefone.replace(/\D/g, '')}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 600;">
                ${servico.telefone}
              </a>
            </div>
            ` : ''}
          </div>

          <button class="btn-agendar" data-servico='${JSON.stringify(servico)}'>
            Agendar
          </button>
        `;
        container.appendChild(card);
      });

      configurarBotoesAgendar();
    });

  function configurarBotoesAgendar() {
    document.querySelectorAll(".btn-agendar").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        try {
          const dataStr = btn.getAttribute("data-servico");
          const servicoSelecionado = JSON.parse(dataStr);
          localStorage.setItem("servicoSelecionado", JSON.stringify(servicoSelecionado));
          window.location.href = "/agendamento";
        } catch (err) {
          console.error("Erro ao processar clique de agendamento:", err);
        }
      });
    });
  }
});