document.addEventListener("DOMContentLoaded", () => {

  const container = document.getElementById("lista-servicos");
  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");

  let servicos = JSON.parse(localStorage.getItem("servicos")) || [];

  function criarCard(servico) {
    return `
      <div class="card" data-categoria="${servico.categoria}">
        
        <span class="tag azul">${servico.categoria}</span>

        <span class="preco">R$ ${servico.preco || "0.00"}</span>

        <h3>${servico.titulo}</h3>

        <p>${servico.descricao || ""}</p>

        <small class="text-gray-500">
          Duração: ${servico.duracao || "-"}h
        </small>

        <button>Agendar</button>
      </div>
    `;
  }

  function render() {
    container.innerHTML = servicos.map(criarCard).join("");
  }

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

    container.innerHTML = filtrados.map(criarCard).join("");
  }

  buscaInput.addEventListener("input", filtrar);
  filtroCategoria.addEventListener("change", filtrar);

  render();
});
