# TODO – Avaliação no login e remoção do perfil

- [ ] Criar rota no `app.py` para exibir avaliação pendente imediatamente após login do cliente (ex.: `/avaliar`), redirecionando para `/servicos` quando não houver pendência.

- [ ] Ajustar fluxo de login (`/autenticar` e `/callback`) para clientes irem para `/avaliar` em vez de `/servicos`.
- [ ] Remover a modal e o script de avaliação de `templates/perfil-cliente.html` (para não aparecer mais no perfil).
- [ ] Garantir que a tela de avaliação redirecione para `/servicos` após salvar ou pular.
- [ ] Rodar/testar: login com pendência e sem pendência; avaliar; pular; verificar sumiço do modal do perfil.

