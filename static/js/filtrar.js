document.addEventListener("DOMContentLoaded", () => {

  const container = document.getElementById("lista-servicos");
  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");

  let servicos = JSON.parse(localStorage.getItem("servicos")) || [];

  // 🔥 CRIA CARD
  function criarCard(servico, index) {
    return `
      <div class="card" data-categoria="${servico.categoria}">
        
        <span class="tag azul">${servico.categoria}</span>

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

        const usuario = localStorage.getItem("usuarioLogado");

        if (!usuario) {
          alert("Você precisa estar logado para agendar!");
          window.location.href = "/login";
          return;
        }

        const servicoSelecionado = listaAtual[i];

        localStorage.setItem(
          "servicoSelecionado",
          JSON.stringify(servicoSelecionado)
        );

        // 👉 vai para página de agendamento
        window.location.href = "/agendamento.html";
      });
    });
  }

  // 🔥 RENDER INICIAL
  function render() {
    container.innerHTML = servicos
      .map((s, i) => criarCard(s, i))
      .join("");

    adicionarEventos();
  }

  // 🔥 FILTRO
  function filtrar() {
    const texto = buscaInput.value.toLowerCase();
    const categoria = filtroCategoria.value;

    const filtrados = servicos.filter(s => {

      const matchTexto =
        s.titulo.toLowerCase().includes(texto) ||
        (s.descricao || "").toLowerCase().includes(texto);

      const matchCategoria =
        categoria === "todas" || s.categoria === categoria;

      return matchTexto && matchCategoria;
    });

    container.innerHTML = filtrados
      .map((s, i) => criarCard(s, i))
      .join("");

    adicionarEventos(filtrados);
  }

  buscaInput.addEventListener("input", filtrar);
  filtroCategoria.addEventListener("change", filtrar);

  render();
});
