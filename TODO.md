<<<<<<< HEAD
# TODO

- [ ] Substituir o ícone do logo no header (`templates/partials/header.html`) pelo arquivo `static/img/agenda-facil.png`.
- [ ] Adicionar favicon `static/img/agenda-facil.png` na aba do navegador em todas as páginas que possuem `<head>` (ex.: `principal.html`, `login.html`, `servicos.html`, `formulario.html`, `agendamento.html`, `painel.html`, `perfil-*.html`, `orcamentos.html`, e templates admin quando aplicável).
- [ ] Testar no navegador: confirmar favicon visível e imagem do header carregando.
=======
# TODO – Avaliação no login e remoção do perfil

- [ ] Criar rota no `app.py` para exibir avaliação pendente imediatamente após login do cliente (ex.: `/avaliar`), redirecionando para `/servicos` quando não houver pendência.

- [ ] Ajustar fluxo de login (`/autenticar` e `/callback`) para clientes irem para `/avaliar` em vez de `/servicos`.
- [ ] Remover a modal e o script de avaliação de `templates/perfil-cliente.html` (para não aparecer mais no perfil).
- [ ] Garantir que a tela de avaliação redirecione para `/servicos` após salvar ou pular.
- [ ] Rodar/testar: login com pendência e sem pendência; avaliar; pular; verificar sumiço do modal do perfil.
>>>>>>> 2c93cb62e5ddee2de250254ebc2baca40a1abf78

