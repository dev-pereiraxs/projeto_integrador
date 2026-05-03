// agenda_facil.js
// Responsabilidade: capturar clique em ".btn-agendar" na tela de serviços,
// salvar o objeto completo (com prestador_email) no localStorage
// e redirecionar para /agendamentos.

document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-agendar");
  if (!btn) return;

  // Verifica login
  if (typeof usuarioLogado === "undefined" || usuarioLogado === "") {
    alert("Você precisa estar logado para agendar!");
    window.location.href = "/login";
    return;
  }

  // Lê o objeto completo do data-servico (colocado pelo filtrar.js)
  let servico;
  try {
    servico = JSON.parse(btn.dataset.servico);
  } catch (err) {
    console.error("[AGENDAR] Erro ao ler data-servico:", err);
    alert("Erro ao selecionar serviço. Tente novamente.");
    return;
  }

  // Garante que prestador_email está presente
  if (!servico.prestador_email) {
    console.warn("[AGENDAR] prestador_email ausente no objeto:", servico);
  } else {
    console.log("[AGENDAR] prestador_email:", servico.prestador_email);
  }

  // Salva no localStorage e redireciona
  localStorage.setItem("servicoSelecionado", JSON.stringify(servico));
  window.location.href = "/agendamentos";
});
