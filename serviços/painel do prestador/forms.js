const form = document.getElementById("form");

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const novoServico = {
    titulo: document.getElementById("nome").value,
    categoria: document.getElementById("categoria").value.toLowerCase(),
    descricao: document.getElementById("descricao").value,
    preco: document.getElementById("preco").value,
    duracao: document.getElementById("duracao").value,
    data: new Date().toLocaleString(),
    status: "pendente"
  };

  const lista = JSON.parse(localStorage.getItem("servicos")) || [];

  lista.push(novoServico);

  localStorage.setItem("servicos", JSON.stringify(lista));

  window.location.href = "sucesso.html";
});
