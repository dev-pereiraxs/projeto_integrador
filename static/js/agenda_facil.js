document.addEventListener("DOMContentLoaded", () => {

  // NOVA TRAVA DE SEGURANÇA:
  const tituloEl = document.getElementById("servico-titulo");
  if (!tituloEl) {
      return; // Se não estiver na tela de agendamento, desliga o JS aqui.
  }

  // PEGA O SERVIÇO DO LOCAL STORAGE
  const servico = JSON.parse(localStorage.getItem("servicoSelecionado"));

  if (!servico) {
    alert("Nenhum serviço selecionado! Escolha um serviço primeiro.");
    // Manda de volta pra vitrine de serviços, pra não dar loop!
    window.location.href = "/servicos";
    return;
  }

  // ELEMENTOS DA TELA (Declarados apenas uma vez!)
  const precoEl = document.getElementById("servico-preco");
  const totalEl = document.getElementById("servico-total");
  const dataEl = document.querySelectorAll(".sum-row-value")[1];
  const confirmBtn = document.querySelector(".confirm-btn");

  const dias = document.querySelectorAll(".cal-day.available");
  const horarios = document.querySelectorAll(".time-btn");

  let dataSelecionada = "";
  let horarioSelecionado = "";

  // PREENCHE O HTML COM OS DADOS DO SERVIÇO
  const precoFormatado = "R$ " + (servico.preco || "0.00");

  tituloEl.textContent = servico.titulo;
  precoEl.textContent = precoFormatado;
  totalEl.textContent = precoFormatado;

  // 🔥 ANIMAÇÃO DIA
  dias.forEach(dia => {
    dia.addEventListener("click", () => {
      dias.forEach(d => d.classList.remove("selected"));
      dia.classList.add("selected");
      dataSelecionada = dia.textContent + " Abr";
      atualizarResumo();
    });
  });

  // 🔥 HORÁRIO
  horarios.forEach(h => {
    h.addEventListener("click", () => {
      horarios.forEach(t => t.classList.remove("selected"));
      h.classList.add("selected");
      horarioSelecionado = h.textContent;
      atualizarResumo();
    });
  });

  function atualizarResumo() {
    if (dataSelecionada && horarioSelecionado) {
      dataEl.textContent = `${dataSelecionada}, ${horarioSelecionado}`;
    }
  }

  // 🔥 RIPPLE EFFECT (Efeito de clique do botão)
  function rippleEffect(e) {
    const button = e.currentTarget;
    const circle = document.createElement("span");
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${e.clientX - button.offsetLeft - radius}px`;
    circle.style.top = `${e.clientY - button.offsetTop - radius}px`;

    const ripple = button.getElementsByClassName("ripple")[0];
    if (ripple) {
      ripple.remove();
    }

    circle.classList.add("ripple");
    button.appendChild(circle);
  }

  confirmBtn.addEventListener("click", rippleEffect);

  // 🔥 CONFIRMAR AGENDAMENTO SALVANDO NO BANCO DE DADOS (MYSQL)
  confirmBtn.addEventListener("click", () => {

    if (!dataSelecionada || !horarioSelecionado) {
      alert("Selecione uma data e horário!");
      return;
    }

    // Coloca o botão em modo "carregando"
    confirmBtn.classList.add("loading");
    confirmBtn.textContent = "Agendando...";

    // Prepara o pacote de dados
    const dadosAgendamento = {
        servico: servico.titulo,
        preco: servico.preco,
        data: dataSelecionada,
        horario: horarioSelecionado
    };

    // Manda os dados para o Python usando fetch
    fetch('/salvar_agendamento', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dadosAgendamento)
    })
    .then(response => response.json())
    .then(data => {
        // Tira o botão do modo carregando
        confirmBtn.classList.remove("loading");
        confirmBtn.textContent = "Confirmar Agendamento";

        if (data.erro) {
            alert("Erro: " + data.erro);
        } else {
            // Deu certo! Mostra a mensagem
            mostrarToast("Agendamento salvo no banco de dados!");

            // Depois de 1.5s, manda para a tela inicial
            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        }
    })
    .catch(erro => {
        console.error("Falha na comunicação com o servidor:", erro);
        alert("Ocorreu um erro de conexão.");
        confirmBtn.classList.remove("loading");
        confirmBtn.textContent = "Confirmar Agendamento";
    });
  });

  // 🔥 FUNÇÃO TOAST (Notificação bonita que tinha sumido do seu código)
  function mostrarToast(msg) {
    const toast = document.createElement("div");
    toast.className = "toast show";
    toast.textContent = msg;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  }

});