/* ==============================
   DADOS (SIMULAÇÃO DE BACKEND)
   ============================== */
const agendamentos = [
  {
    titulo: "Reparo de Computador",
    categoria: "Tecnologia / TI",
    preco: 100,
    status: "pendentes",
    classe: "azul"
  },
  {
    titulo: "Troca de Óleo",
    categoria: "Mecânica",
    preco: 120,
    status: "concluidos",
    classe: "verde"
  }
];

/* ==============================
   FUNÇÃO DE RENDERIZAÇÃO
   ============================== */
function render(tab) {

  const container = document.getElementById("cards");
  const empty = document.getElementById("empty");

  // limpa tela
  container.innerHTML = "";

  // filtra os dados pela aba
  const filtrados = agendamentos.filter(a => a.status === tab);

  // se não tiver dados
  if (filtrados.length === 0) {
    empty.classList.remove("hidden");
    return;
  } else {
    empty.classList.add("hidden");
  }

  // cria os cards dinamicamente
  filtrados.forEach(item => {

    const card = document.createElement("div");
    card.classList.add("card");

    card.innerHTML = `
      <!-- TAG -->
      <span class="tag ${item.classe}">
        ${item.categoria}
      </span>

      <!-- PREÇO -->
      <span class="preco">
        R$ ${item.preco}
      </span>

      <!-- TÍTULO -->
      <h3 class="text-lg font-semibold">
        ${item.titulo}
      </h3>

      <!-- BOTÃO -->
      <button class="btn">
        Agendar
      </button>
    `;

    container.appendChild(card);
  });
}

/* ==============================
   CONTROLE DAS ABAS
   ============================== */
const tabs = document.querySelectorAll(".tab");

tabs.forEach(tab => {
  tab.addEventListener("click", () => {

    // remove active
    tabs.forEach(t => t.classList.remove("active"));

    // adiciona active
    tab.classList.add("active");

    // renderiza
    render(tab.dataset.tab);
  });
});

/* ==============================
   INICIALIZAÇÃO
   ============================== */
render("pendentes");
