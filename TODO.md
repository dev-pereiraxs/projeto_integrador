# Agenda Fácil — Painel Administrativo (Admin)

## Plano aprovado ✅

### Passo 1 — Infra de Admin (back-end)
- [ ] 1.1 Implementar autenticação/autorizações de administrador
  - [ ] Criar checagem de sessão (ex.: `session['tipo_usuario']=='admin'`) e/ou validação em tabela `admins`
  - [ ] Criar decorators/helpers para bloquear acesso de não-admin
- [ ] 1.2 Criar rotas admin
  - [ ] `/admin` (dashboard)
  - [ ] `/admin/login` (ou reaproveitar `/autenticar` com detecção admin)
  - [ ] APIs base: `/admin/api/metrics` (métricas gerais)
- [ ] 1.3 Registrar ações em `admin_logs`
  - [ ] Logar login admin e ações principais do admin (quando existirem)

### Passo 2 — Dashboard administrativo
- [ ] 2.1 Criar template `templates/admin/dashboard.html`
  - [ ] Cards com métricas
  - [ ] Contêiner de gráficos
- [ ] 2.2 Criar JS `static/js/admin/dashboard.js`
  - [ ] Buscar dados em `/admin/api/metrics`
  - [ ] Atualização periódica (quase tempo real)
  - [ ] Renderizar gráficos (Chart.js via CDN)
- [ ] 2.3 Criar CSS `static/admin.css` (ou complementar `static/painel.css`)

### Passo 3 — Módulo de Solicitações (agendamentos)
- [ ] 3.1 Listagem com filtros e modal/rota de detalhes
- [ ] 3.2 Atualização de status com histórico/log
- [ ] 3.3 Excluir solicitações indevidas

### Passo 4 — Módulos Usuários/Prestadores
- [ ] 4.1 Clientes (bloqueio/desbloqueio, edição, exclusão, histórico)
- [ ] 4.2 Prestadores (aprovação/reprovação, verificar docs, bloquear, avaliações, ranking)

### Passo 5 — Denúncias e Suporte
- [ ] 5.1 Denúncias (listagem, filtros, status)
- [ ] 5.2 Tickets (listar, responder, resolver)

### Passo 6 — Categorias, Notificações, Configurações, Segurança
- [ ] 6.1 Categorias CRUD (ícone e cor)
- [ ] 6.2 Notificações (globais/prestador/admin)
- [ ] 6.3 Configurações (logo/cores/e-mails e integrações)
- [ ] 6.4 Permissões e níveis de admin

## Observações técnicas
- O `db_servicos.sql` já contém tabelas para admin, logs, denúncias, tickets, notificações e categorias.
- O `app.py` atual ainda não implementa essas rotas.
- Para ações completas (aprovar prestadores, bloquear contas etc.), pode ser necessário adicionar campos/tabelas extras no MySQL caso não existam ainda.

