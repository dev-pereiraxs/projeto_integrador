document.addEventListener("DOMContentLoaded", () => {

  const servico = JSON.parse(localStorage.getItem("servicoSelecionado"));

  if (!servico) {
    alert("Nenhum serviço selecionado!");
    window.location.href = "/servicos";
    return;
  }

  // ELEMENTOS
  const tituloEl = document.getElementById("servico-titulo");
  const precoEl = document.getElementById("servico-preco");
  const totalEl = document.getElementById("servico-total");
  const dataEl = document.querySelectorAll(".sum-row-value")[1];
  const confirmBtn = document.querySelector(".confirm-btn");

  const dias = document.querySelectorAll(".cal-day.available");
  const horarios = document.querySelectorAll(".time-btn");

  let dataSelecionada = "";
  let horarioSelecionado = "";

  // PREENCHE
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

  // 🔥 RIPPLE EFFECT
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

  // aplica ripple no botão
  confirmBtn.addEventListener("click", rippleEffect);

  // 🔥 CONFIRMAR AGENDAMENTO COM LOADING
  confirmBtn.addEventListener("click", () => {

    if (!dataSelecionada || !horarioSelecionado) {
      alert("Selecione uma data e horário!");
      return;
    }

    confirmBtn.classList.add("loading");
    confirmBtn.textContent = "Agendando...";

    setTimeout(() => {

      const agendamento = {
        servico: servico.titulo,
        preco: servico.preco,
        data: dataSelecionada,
        horario: horarioSelecionado,
        criadoEm: new Date().toLocaleString()
      };

      const lista = JSON.parse(localStorage.getItem("agendamentos")) || [];

      lista.push(agendamento);

      localStorage.setItem("agendamentos", JSON.stringify(lista));

      confirmBtn.classList.remove("loading");
      confirmBtn.textContent = "Confirmar Agendamento";

      mostrarToast("Agendamento realizado com sucesso!");

      setTimeout(() => {
        window.location.href = "/perfil";
      }, 1500);

    }, 1500); // simula loading
  });

  // 🔥 TOAST
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
