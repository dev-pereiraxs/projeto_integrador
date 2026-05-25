document.addEventListener("DOMContentLoaded", () => {
  const inputBusca = document.getElementById("busca");
  const selectCategoria = document.getElementById("filtroCategoria");
  const cards = document.querySelectorAll(".card");

  function filtrarServicos() {
    // Pega o termo digitado e a categoria selecionada, limpando acentos
    const termoBusca = inputBusca ? inputBusca.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") : "";
    const categoriaFiltro = selectCategoria ? selectCategoria.value.toLowerCase() : "todas";

    cards.forEach(card => {
      // 1. Pega os textos visíveis no card (Título e Descrição)
      const tituloEl = card.querySelector("h3");
      const descEl = card.querySelector("p");

      const titulo = tituloEl ? tituloEl.textContent.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") : "";
      const descricao = descEl ? descEl.textContent.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") : "";

      // 2. Descobre a categoria lendo o JSON que já existe no botão "Agendar"
      let categoriaCard = "";
      const btnAgendar = card.querySelector(".btn-agendar");

      if (btnAgendar) {
        try {
          const servicoData = JSON.parse(btnAgendar.getAttribute("data-servico"));

          // Pega a área do banco de dados e limpa os acentos
          let area = servicoData.area_atuacao || servicoData.areas_atuacao || "";
          area = area.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

          // 🎯 CORRETOR INTELIGENTE: Transforma as variações para bater com o filtro
          if (area.includes("ti") || area.includes("tecnologia")) {
            categoriaCard = "tecnologia";
          } else if (area.includes("hidraulica") || area.includes("hydraulica")) {
            categoriaCard = "hidraulica";
          } else {
            categoriaCard = area;
          }
        } catch (e) {
          console.error("Erro ao ler dados do serviço para o filtro", e);
        }
      }

      // 3. Verifica se o card atende às condições do filtro e da busca
      const matchBusca = titulo.includes(termoBusca) || descricao.includes(termoBusca);
      const matchCategoria = (categoriaFiltro === "todas") || (categoriaCard === categoriaFiltro);

      // 4. Mostra ou esconde o card
      if (matchBusca && matchCategoria) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  }

  // Aciona o filtro toda vez que o usuário digitar ou mudar a categoria
  if (inputBusca) inputBusca.addEventListener("input", filtrarServicos);
  if (selectCategoria) selectCategoria.addEventListener("change", filtrarServicos);
});