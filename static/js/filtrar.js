document.addEventListener("DOMContentLoaded", () => {

  const container = document.getElementById("lista-servicos");
  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");
  const pagination = document.getElementById("pagination");

  // LISTA COMPLETA
  let servicos = [];

  // LISTA FILTRADA
  let servicosFiltrados = [];

  // PAGINAÇÃO
  const itensPorPagina = 12;
  let paginaAtual = 1;

  // 🔥 BUSCA SERVIÇOS NO MYSQL
  function carregarServicosDoBanco() {
    fetch("/api/listar_servicos")
      .then(response => response.json())
      .then(data => {

        servicos = data;
        servicosFiltrados = data;

        render();
      })
      .catch(erro => {

        console.error("Erro ao buscar serviços:", erro);

        container.innerHTML = `
          <p class="col-span-full text-center text-red-500">
            Erro ao carregar os serviços.
          </p>
        `;
      });
  }

  // 🔥 CRIA CARD
  function criarCard(servico, index) {

    const categoriaNome =
      servico.area_atuacao ||
      servico.categoria ||
      "Geral";

    return `
      <div class="card" data-categoria="${categoriaNome}">

        <span class="tag azul">
          ${categoriaNome}
        </span>

        <span class="preco">
          R$ ${servico.preco || "0.00"}
        </span>

        <h3>
          ${servico.titulo || "Sem título"}
        </h3>

        <p>
          ${servico.descricao || ""}
        </p>

      </div>
    `;
  }

  // 🔥 RENDERIZA SERVIÇOS
  function render() {

    container.innerHTML = "";

    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;

    const itensPagina = servicosFiltrados.slice(inicio, fim);

    if (itensPagina.length === 0) {

      container.innerHTML = `
        <p class="col-span-full text-center text-gray-500">
          Nenhum serviço encontrado.
        </p>
      `;

      return;
    }

    // Renderiza cards com botões (Agendar) para manter compatibilidade com o fluxo atual.
    itensPagina.forEach((servico, index) => {
      // criarCard() atual não inclui o botão; adicionamos aqui.
      const card = document.createElement('div');
      card.innerHTML = criarCard(servico, index);

      const cardEl = card.firstElementChild;
      if (cardEl) {
        const btn = document.createElement('button');
        btn.className = 'btn-agendar';
        btn.textContent = 'Agendar';
        // usa o dataset.servico porque a agenda_facil.js lê btn.dataset.servico
        btn.dataset.servico = JSON.stringify(servico);

        // garante o redirecionamento com os dados do card
        btn.addEventListener('click', (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          try {
            localStorage.setItem('servicoSelecionado', JSON.stringify(servico));
          } catch (e) {}
          // rota correta no backend (app.py)
          window.location.href = '/agendamentos';
        });



        cardEl.appendChild(btn);
      }


      container.appendChild(cardEl);
    });


    renderPagination();
  }

  // 🔥 PAGINAÇÃO
  function renderPagination() {

    pagination.innerHTML = "";

    const totalPaginas = Math.ceil(servicosFiltrados.length / itensPorPagina);

    for (let i = 1; i <= totalPaginas; i++) {

      pagination.innerHTML += `
        <button
          class="px-4 py-2 rounded bg-blue-500 text-white mx-1"
          onclick="trocarPagina(${i})"
        >
          ${i}
        </button>
      `;
    }
  }

  // 🔥 TROCAR PÁGINA
  window.trocarPagina = function(pagina) {

    paginaAtual = pagina;

    render();
  };

  // 🔥 FILTRO DE BUSCA
  buscaInput.addEventListener("input", aplicarFiltros);

  // 🔥 FILTRO DE CATEGORIA
  filtroCategoria.addEventListener("change", aplicarFiltros);

  function aplicarFiltros() {

    const textoBusca = buscaInput.value.toLowerCase();

    const categoriaSelecionada =
      filtroCategoria.value.toLowerCase();

    servicosFiltrados = servicos.filter(servico => {

      const titulo =
        (servico.titulo || "").toLowerCase();

      const descricao =
        (servico.descricao || "").toLowerCase();

      const categoria =
        (
          servico.area_atuacao ||
          servico.categoria ||
          ""
        ).toLowerCase();

      const correspondeBusca =
        titulo.includes(textoBusca) ||
        descricao.includes(textoBusca);

      const correspondeCategoria =
        categoriaSelecionada === "" ||
        categoria === categoriaSelecionada;

      return correspondeBusca && correspondeCategoria;
    });

    paginaAtual = 1;

    render();
  }

  // 🔥 INICIA
  carregarServicosDoBanco();

});

