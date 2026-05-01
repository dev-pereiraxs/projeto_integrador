document.addEventListener("DOMContentLoaded", () => {

  const container = document.getElementById("lista-servicos");
  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");

  // Agora começa vazio. O banco de dados é quem vai preencher!
  let servicos = [];

  // 🔥 BUSCA OS DADOS NO PYTHON (MYSQL)
  function carregarServicosDoBanco() {
    fetch('/api/listar_servicos')
      .then(response => response.json())
      .then(data => {
        servicos = data; // Salva os serviços que vieram do banco
        render();        // Manda desenhar os cards na tela
      })
      .catch(erro => {
        console.error("Erro ao buscar serviços:", erro);
        container.innerHTML = "<p class='col-span-full text-center text-red-500'>Erro ao carregar os serviços.</p>";
      });
  }

  // 🔥 CRIA CARD
  function criarCard(servico, index) {
    // No banco salvamos como "area_atuacao", então ajustamos aqui
    const categoriaNome = servico.area_atuacao || servico.categoria || "Geral";

    return `
      <div class="card" data-categoria="${categoriaNome}">
        <span class="tag azul">${categoriaNome}</span>
        <span class="preco">R$ ${servico.preco || "0.00"}</span>
        <h3>${servico.titulo}</h3>
        <p>${servico.descricao || ""}</p>
        <small class="text-gray-500">
          Duração: ${servico.duracao || "-"}h
        </small>
        <button class="btn-agendar" data-index="${index}">
          Agendar
        </button>
      </div>
    `;
  }

  // 🔥 ADICIONA EVENTO NOS BOTÕES
  function adicionarEventos(listaAtual = servicos) {
    const botoes = document.querySelectorAll(".btn-agendar");

    botoes.forEach((btn, i) => {
      btn.addEventListener("click", () => {

        // Usamos a variável que o Flask injeta no HTML
        if (typeof usuarioLogado === 'undefined' || usuarioLogado === "") {
          alert("Você precisa estar logado para agendar!");
          window.location.href = "/login";
          return;
        }

        const servicoSelecionado = listaAtual[i];

        // Aqui nós mantemos o localStorage, pois a tela de Agendamentos (calendário)
        // ainda precisa saber em qual card você clicou!
        localStorage.setItem(
          "servicoSelecionado",
          JSON.stringify(servicoSelecionado)
        );

        // Vai para a página de agendamento
        window.location.href = "/agendamentos";
      });
    });
  }

  // 🔥 RENDER INICIAL
  function render() {
    if (servicos.length === 0) {
      container.innerHTML = "<p class='col-span-full text-center text-gray-500'>Nenhum serviço disponível no momento.</p>";
      return;
    }

    container.innerHTML = servicos
      .map((s, i) => criarCard(s, i))
      .join("");

    adicionarEventos();
  }

  // 🔥 FILTRO
  function filtrar() {
    const texto = buscaInput.value.toLowerCase();
    const categoria = filtroCategoria.value.toLowerCase();

    const filtrados = servicos.filter(s => {
      const cat = (s.area_atuacao || s.categoria || "").toLowerCase();

      const matchTexto =
        s.titulo.toLowerCase().includes(texto) ||
        (s.descricao || "").toLowerCase().includes(texto);

      const matchCategoria =
        categoria === "todas" || cat === categoria;

      return matchTexto && matchCategoria;
    });

    container.innerHTML = filtrados
      .map((s, i) => criarCard(s, i))
      .join("");

    adicionarEventos(filtrados);
  }

  buscaInput.addEventListener("input", filtrar);
  filtroCategoria.addEventListener("change", filtrar);

  // 🔥 DÁ O START NA APLICAÇÃO (Chama a função de buscar no banco)
  carregarServicosDoBanco();
});