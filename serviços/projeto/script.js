document.addEventListener("DOMContentLoaded", () => {

  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");
  const cards = document.querySelectorAll(".card");

  // 🔧 função para normalizar texto (remove acento)
  function normalizar(texto) {
    return texto
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function filtrarServicos() {
    const texto = normalizar(buscaInput.value);
    const categoria = normalizar(filtroCategoria.value);

    cards.forEach(card => {
      const titulo = normalizar(card.querySelector("h3").textContent);
      const descricao = normalizar(card.querySelector("p").textContent);
      const categoriaCard = normalizar(card.dataset.categoria);

      const matchTexto =
        titulo.includes(texto) || descricao.includes(texto);

      const matchCategoria =
        categoria === "todas" || categoria === categoriaCard;

      card.style.display = (matchTexto && matchCategoria)
        ? "block"
        : "none";
    });
  }

  buscaInput.addEventListener("input", filtrarServicos);
  filtroCategoria.addEventListener("change", filtrarServicos);

});
