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

      let categoriaCard = "";
      const btnAgendar = card.querySelector(".btn-agendar");

      if (btnAgendar) {
        // 2. A "Marretada": Escaneia o código HTML bruto do botão para achar a categoria
        // Isso ignora qualquer erro de aspas ou JSON quebrado vindo do Flask!
        const btnHtmlStr = btnAgendar.outerHTML.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

        // 3. Corretor Inteligente e Mapeamento Direto
        if (btnHtmlStr.includes("tecnologia") || btnHtmlStr.includes("ti")) {
          categoriaCard = "tecnologia";
        } else if (btnHtmlStr.includes("hidraulica") || btnHtmlStr.includes("hydraulica")) {
          categoriaCard = "hidraulica";
        } else if (btnHtmlStr.includes("mecanica")) {
          categoriaCard = "mecanica";
        } else if (btnHtmlStr.includes("eletrica")) {
          categoriaCard = "eletrica";
        } else if (btnHtmlStr.includes("reformas")) {
          categoriaCard = "reformas";
        } else if (btnHtmlStr.includes("limpeza")) {
          categoriaCard = "limpeza";
        }
      }

      // 4. Verifica se o card atende às condições do filtro e da busca
      const matchBusca = titulo.includes(termoBusca) || descricao.includes(termoBusca);
      const matchCategoria = (categoriaFiltro === "todas") || (categoriaCard === categoriaFiltro);

      // 5. Mostra ou esconde o card (usando "flex" para preservar o alinhamento dos botões)
      if (matchBusca && matchCategoria) {
        card.style.display = "flex";
      } else {
        card.style.display = "none";
      }
    });
  }

  // Aciona o filtro toda vez que o usuário digitar ou mudar a categoria
  if (inputBusca) inputBusca.addEventListener("input", filtrarServicos);
  if (selectCategoria) selectCategoria.addEventListener("change", filtrarServicos);

  // Força o filtro a rodar uma vez assim que a página carregar
  filtrarServicos();
});