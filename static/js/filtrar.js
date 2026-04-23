document.addEventListener("DOMContentLoaded", () => {

  const buscaInput = document.getElementById("busca");
  const filtroCategoria = document.getElementById("filtroCategoria");
  const cards = document.querySelectorAll(".card");

  function filtrarServicos() {
    const texto = buscaInput.value.toLowerCase();
    const categoria = filtroCategoria.value;

    cards.forEach(card => {
      const titulo = card.querySelector("h3").textContent.toLowerCase();
      const descricao = card.querySelector("p").textContent.toLowerCase();
      const categoriaCard = card.dataset.categoria;

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
