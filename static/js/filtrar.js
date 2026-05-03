document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("lista-servicos");
  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");

  let servicos = [];

  // ── BUSCA DO BANCO ────────────────────────────────────────
  function carregarServicosDoBanco() {
    fetch("/api/listar_servicos")
      .then((r) => r.json())
      .then((data) => {
        servicos = data;
        render(servicos);
      })
      .catch((err) => {
        console.error("Erro ao buscar serviços:", err);
        container.innerHTML =
          "<p class='col-span-full text-center text-red-500'>Erro ao carregar os serviços.</p>";
      });
  }

  // ── CRIA CARD ─────────────────────────────────────────────
  function criarCard(servico) {
    const categoria = servico.area_atuacao || servico.categoria || "Geral";
    // Serializa o objeto completo (com prestador_email) no data-servico
    const dadosJson = JSON.stringify(servico).replace(/'/g, "&#39;");

    return `
      <div class="card" data-categoria="${categoria}">
        <span class="tag azul">${categoria}</span>
        <span class="preco">R$ ${servico.preco || "0.00"}</span>
        <h3>${servico.titulo}</h3>
        <p>${servico.descricao || ""}</p>
        <small class="text-gray-500">Duração: ${servico.duracao || "-"}h</small>
        <small class="text-gray-400">Prestador: ${servico.nome || ""} ${servico.sobrenome || ""}</small>
        <button class="btn-agendar" data-servico='${dadosJson}'>
          Agendar
        </button>
      </div>
    `;
  }

  // ── RENDER ────────────────────────────────────────────────
  function render(lista) {
    if (!lista || lista.length === 0) {
      container.innerHTML =
        "<p class='col-span-full text-center text-gray-500'>Nenhum serviço disponível no momento.</p>";
      return;
    }
    container.innerHTML = lista.map((s) => criarCard(s)).join("");
  }

  // ── FILTRO ────────────────────────────────────────────────
  function filtrar() {
    const texto = buscaInput.value.toLowerCase();
    const categoria = filtroCategoria.value.toLowerCase();

    const filtrados = servicos.filter((s) => {
      const cat = (s.area_atuacao || s.categoria || "").toLowerCase();
      const matchTexto =
        s.titulo.toLowerCase().includes(texto) ||
        (s.descricao || "").toLowerCase().includes(texto);
      const matchCategoria = categoria === "todas" || cat === categoria;
      return matchTexto && matchCategoria;
    });

    render(filtrados);
  }

  buscaInput.addEventListener("input", filtrar);
  filtroCategoria.addEventListener("change", filtrar);

  carregarServicosDoBanco();
});
