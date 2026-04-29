const form = document.getElementById("form");

const categorias = {
  mecanica: [
    "Troca de óleo",
    "Alinhamento e balanceamento",
    "Revisão geral",
    "Troca de pastilhas de freio",
    "Diagnóstico eletrônico",
    "Troca de bateria"
  ],
  eletrica: [
    "Instalação de tomadas",
    "Troca de disjuntor",
    "Instalação de chuveiro elétrico",
    "Manutenção elétrica residencial",
    "Instalação de luminárias",
    "Correção de curto-circuito"
  ],
  tecnologia: [
    "Formatação de computador",
    "Instalação de software",
    "Montagem de PC",
    "Remoção de vírus",
    "Configuração de rede Wi-Fi",
    "Suporte técnico remoto"
  ],
  reformas: [
    "Pintura de paredes",
    "Instalação de drywall",
    "Colocação de piso",
    "Reforma de banheiro",
    "Pequenos reparos gerais",
    "Impermeabilização"
  ],
  hidraulica: [
    "Desentupimento",
    "Troca de torneira",
    "Conserto de vazamento",
    "Instalação de vaso sanitário",
    "Limpeza de caixa d’água",
    "Instalação de chuveiro"
  ],
  limpeza: [
    "Limpeza residencial",
    "Limpeza pós-obra",
    "Limpeza de estofados",
    "Limpeza de vidros",
    "Limpeza pesada",
    "Higienização de colchão"
  ]
};

const descricoes = {
  "Troca de óleo": "Substituição do óleo do motor para melhor desempenho e durabilidade.",
  "Alinhamento e balanceamento": "Ajuste das rodas para garantir estabilidade e evitar desgaste irregular.",
  "Revisão geral": "Verificação completa dos sistemas do veículo.",
  "Troca de pastilhas de freio": "Substituição das pastilhas para garantir segurança na frenagem.",
  "Diagnóstico eletrônico": "Análise via scanner para identificar problemas eletrônicos.",
  "Troca de bateria": "Substituição da bateria automotiva.",

  "Instalação de tomadas": "Instalação segura de pontos de energia elétrica.",
  "Troca de disjuntor": "Substituição de disjuntores para proteção elétrica.",
  "Instalação de chuveiro elétrico": "Instalação completa com segurança elétrica.",
  "Manutenção elétrica residencial": "Reparos e ajustes em instalações elétricas.",
  "Instalação de luminárias": "Montagem e instalação de iluminação.",
  "Correção de curto-circuito": "Identificação e correção de falhas elétricas.",

  "Formatação de computador": "Reinstalação do sistema operacional.",
  "Instalação de software": "Instalação e configuração de programas.",
  "Montagem de PC": "Montagem personalizada de computadores.",
  "Remoção de vírus": "Limpeza de ameaças e proteção do sistema.",
  "Configuração de rede Wi-Fi": "Instalação e otimização de redes sem fio.",
  "Suporte técnico remoto": "Atendimento técnico à distância.",

  "Pintura de paredes": "Pintura interna ou externa com acabamento profissional.",
  "Instalação de drywall": "Montagem de paredes e divisórias.",
  "Colocação de piso": "Instalação de pisos diversos.",
  "Reforma de banheiro": "Reforma completa ou parcial.",
  "Pequenos reparos gerais": "Ajustes e consertos diversos.",
  "Impermeabilização": "Proteção contra infiltrações.",

  "Desentupimento": "Desobstrução de tubulações.",
  "Troca de torneira": "Substituição e instalação de torneiras.",
  "Conserto de vazamento": "Correção de vazamentos hidráulicos.",
  "Instalação de vaso sanitário": "Instalação completa do equipamento.",
  "Limpeza de caixa d’água": "Higienização completa do reservatório.",
  "Instalação de chuveiro": "Instalação hidráulica do chuveiro.",

  "Limpeza residencial": "Limpeza geral de ambientes residenciais.",
  "Limpeza pós-obra": "Remoção de sujeira após construção.",
  "Limpeza de estofados": "Higienização profunda de sofás e cadeiras.",
  "Limpeza de vidros": "Limpeza profissional de janelas.",
  "Limpeza pesada": "Limpeza intensiva de ambientes.",
  "Higienização de colchão": "Remoção de ácaros e sujeiras."
};

const selectCategoria = document.getElementById("categoria");
const selectSubcategoria = document.getElementById("subcategoria");
const descricao = document.getElementById("descricao");

// Atualiza subcategorias
selectCategoria.addEventListener("change", () => {
  const valor = selectCategoria.value.toLowerCase();
  const lista = categorias[valor];

  selectSubcategoria.innerHTML = "";

  lista.forEach(servico => {
    const option = document.createElement("option");
    option.value = servico;
    option.textContent = servico;
    selectSubcategoria.appendChild(option);
  });

  descricao.value = "";
});

// Preenche descrição automática
selectSubcategoria.addEventListener("change", () => {
  const servico = selectSubcategoria.value;
  descricao.value = descricoes[servico] || "";
});

// Submit
form.addEventListener("submit", (e) => {
  e.preventDefault();

  const novoServico = {
    titulo: selectSubcategoria.value,
    categoria: selectCategoria.value.toLowerCase(),
    descricao: descricao.value,
    preco: document.getElementById("preco").value,
    duracao: document.getElementById("duracao").value,
    data: new Date().toLocaleString(),
    status: "publicado"
  };

  const lista = JSON.parse(localStorage.getItem("servicos")) || [];

  lista.push(novoServico);

  localStorage.setItem("servicos", JSON.stringify(lista));

  window.location.href = "/sucesso-servico";
});