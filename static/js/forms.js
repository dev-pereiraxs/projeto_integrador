const form = document.getElementById("form");

const categorias = {
  mecanica: [
    "Troca de óleo",
    "Alinhamento e balanceamento",
    "Revisão geral",
    "Troca de pastilhas de freio",
    "Diagnóstico eletrônico",
    "Troca de bateria",
    "Troca de correia dentada",
    "Troca de embreagem",
    "Revisão de suspensão",
    "Troca de amortecedores",
    "Limpeza de bicos injetores",
    "Troca de filtro de ar",
    "Troca de filtro de combustível",
    "Revisão de ar-condicionado automotivo"
  ],

  eletrica: [
    "Instalação de tomadas",
    "Troca de disjuntor",
    "Instalação de chuveiro elétrico",
    "Manutenção elétrica residencial",
    "Instalação de luminárias",
    "Correção de curto-circuito",
    "Instalação de quadro elétrico",
    "Passagem de fiação",
    "Instalação de ventilador de teto",
    "Instalação de sensores de presença",
    "Aterramento elétrico",
    "Instalação de campainha",
    "Instalação de fita LED"
  ],

  tecnologia: [
    "Formatação de computador",
    "Instalação de software",
    "Montagem de PC",
    "Remoção de vírus",
    "Configuração de rede Wi-Fi",
    "Suporte técnico remoto",
    "Upgrade de hardware",
    "Troca de HD/SSD",
    "Instalação de impressora",
    "Backup de dados",
    "Recuperação de arquivos",
    "Configuração de e-mail",
    "Instalação de câmeras de segurança"
  ],

  reformas: [
    "Pintura de paredes",
    "Instalação de drywall",
    "Colocação de piso",
    "Reforma de banheiro",
    "Pequenos reparos gerais",
    "Impermeabilização",
    "Reforma de cozinha",
    "Instalação de rodapé",
    "Aplicação de gesso",
    "Troca de portas",
    "Instalação de janelas",
    "Reboco e acabamento",
    "Demolição leve"
  ],

  hidraulica: [
    "Desentupimento",
    "Troca de torneira",
    "Conserto de vazamento",
    "Instalação de vaso sanitário",
    "Limpeza de caixa d’água",
    "Instalação de chuveiro",
    "Instalação de caixa d’água",
    "Troca de encanamento",
    "Instalação de bomba d’água",
    "Revisão hidráulica geral",
    "Instalação de filtro de água",
    "Conserto de descarga",
    "Instalação de pia"
  ],

  limpeza: [
    "Limpeza residencial",
    "Limpeza pós-obra",
    "Limpeza de estofados",
    "Limpeza de vidros",
    "Limpeza pesada",
    "Higienização de colchão",
    "Limpeza de sofá",
    "Limpeza de tapetes",
    "Limpeza de cozinha",
    "Limpeza de banheiro",
    "Limpeza de escritório",
    "Limpeza pré-mudança",
    "Limpeza pós-mudança"
  ]
};

const descricoes = {
  "Troca de óleo": "Substituição completa do óleo do motor e filtro, garantindo melhor desempenho, menor desgaste e maior durabilidade do veículo.",
  "Alinhamento e balanceamento": "Ajuste das rodas para melhorar a estabilidade, evitar desgaste irregular dos pneus e aumentar a segurança.",
  "Revisão geral": "Inspeção completa dos sistemas do veículo, incluindo motor, freios, suspensão e parte elétrica.",
  "Troca de pastilhas de freio": "Substituição das pastilhas para garantir eficiência na frenagem e segurança.",
  "Diagnóstico eletrônico": "Análise com scanner para identificar falhas eletrônicas no veículo.",
  "Troca de bateria": "Substituição da bateria com testes do sistema elétrico.",

  "Instalação de tomadas": "Instalação segura de pontos de energia conforme normas técnicas.",
  "Troca de disjuntor": "Substituição de disjuntores para proteção contra sobrecargas.",
  "Instalação de chuveiro elétrico": "Instalação completa com verificação de segurança elétrica.",
  "Manutenção elétrica residencial": "Reparos e ajustes em instalações elétricas domésticas.",
  "Instalação de luminárias": "Montagem e instalação com acabamento profissional.",
  "Correção de curto-circuito": "Identificação e solução de falhas elétricas.",

  "Formatação de computador": "Reinstalação do sistema operacional com otimização.",
  "Instalação de software": "Instalação e configuração de programas.",
  "Montagem de PC": "Montagem personalizada com configuração completa.",
  "Remoção de vírus": "Eliminação de ameaças e proteção do sistema.",
  "Configuração de rede Wi-Fi": "Instalação e melhoria de redes sem fio.",
  "Suporte técnico remoto": "Atendimento técnico à distância.",

  "Pintura de paredes": "Pintura profissional com acabamento uniforme.",
  "Instalação de drywall": "Montagem de divisórias com estrutura adequada.",
  "Colocação de piso": "Instalação de diversos tipos de pisos.",
  "Reforma de banheiro": "Reforma completa ou parcial.",
  "Pequenos reparos gerais": "Serviços rápidos de manutenção.",
  "Impermeabilização": "Proteção contra infiltrações e umidade.",

  "Desentupimento": "Desobstrução de tubulações com equipamentos adequados.",
  "Troca de torneira": "Instalação ou substituição com vedação correta.",
  "Conserto de vazamento": "Correção de vazamentos hidráulicos.",
  "Instalação de vaso sanitário": "Instalação completa com ajuste e vedação.",
  "Limpeza de caixa d’água": "Higienização completa do reservatório.",
  "Instalação de chuveiro": "Instalação hidráulica com testes.",

  "Limpeza residencial": "Limpeza completa de ambientes.",
  "Limpeza pós-obra": "Remoção de resíduos de construção.",
  "Limpeza de estofados": "Higienização profunda de tecidos.",
  "Limpeza de vidros": "Limpeza profissional de superfícies de vidro.",
  "Limpeza pesada": "Limpeza intensiva de ambientes.",
  "Higienização de colchão": "Remoção de ácaros e sujeiras."
};

const selectCategoria = document.getElementById("categoria");
const selectSubcategoria = document.getElementById("subcategoria");
const descricao = document.getElementById("descricao");

//  bloqueia edição manual
descricao.setAttribute("readonly", true);

// Atualiza subcategorias
selectCategoria.addEventListener("change", () => {
  const valor = selectCategoria.value.toLowerCase();
  const lista = categorias[valor] || [];

  selectSubcategoria.innerHTML = "<option value=''>Selecione um serviço</option>";

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

  descricao.value = descricoes[servico] ||
    `Serviço profissional de ${servico.toLowerCase()}, realizado com qualidade, segurança e atenção aos detalhes.`;
});

// Menu mobile

const menuToggle = document.getElementById("menuToggle");
const navMenu = document.getElementById("navMenu");

if (menuToggle && navMenu) {
  menuToggle.addEventListener("click", () => {
    navMenu.classList.toggle("active");
  });
}

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const btnSubmit = form.querySelector("button");
  btnSubmit.textContent = "Cadastrando...";
  btnSubmit.disabled = true;

  const novoServico = {
    titulo: selectSubcategoria.value,
    categoria: selectCategoria.value.toLowerCase(),
    descricao: descricao.value,
    preco: document.getElementById("preco").value,
    duracao: document.getElementById("duracao").value
  };

  fetch('/salvar_servico_prestador', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(novoServico)
  })
    .then(response => response.json())
    .then(data => {
      btnSubmit.textContent = "+ Cadastrar Serviço";
      btnSubmit.disabled = false;

      if (data.erro) {
        alert("Erro: " + data.erro);
      } else {
        alert("Sucesso! Serviço salvo.");
        window.location.href = "/sucesso-agendamento";
      }
    })
    .catch(erro => {
      console.error("Erro:", erro);
      alert("Erro de conexão.");
      btnSubmit.textContent = "+ Cadastrar Serviço";
      btnSubmit.disabled = false;
    });
});