/* dashboard.js — Admin Agenda Fácil */
'use strict';

// ── Chart instances ──────────────────────────────────────────────────────────
let _chartStatus = null;
let _chartSolicitations = null;
let _chartTopPrestadores = null;

// ── Helpers ──────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

function setText(id, value) {
  const node = $(id);
  if (node) node.textContent = (value ?? 0).toLocaleString('pt-BR');
}

// ── Chart: status doughnut ────────────────────────────────────────────────────
function renderChartStatus(statusCounts) {
  const ctx = $('chart_status');
  if (!ctx) return;

  const STATUS_LABELS = ['pendente', 'em_andamento', 'concluido', 'cancelado'];
  const STATUS_NAMES = ['Pendente', 'Em andamento', 'Concluído', 'Cancelado'];
  const COLORS = ['#f59e0b', '#0ea5e9', '#10b981', '#ef4444'];

  const data = STATUS_LABELS.map((k) => statusCounts[k] ?? 0);

  if (_chartStatus) _chartStatus.destroy();

  _chartStatus = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: STATUS_NAMES,
      datasets: [{
        data,
        backgroundColor: COLORS,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 6,
      }],
    },
    options: {
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            borderRadius: 3,
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 14,
            font: { family: 'DM Sans', size: 12 },
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.toLocaleString('pt-BR')} agendamentos`,
          },
        },
      },
    },
  });
}

// ── Chart: solicitations line ─────────────────────────────────────────────────
function renderChartSolicitations(last7) {
  const ctx = $('chart_solicitations');
  if (!ctx) return;

  const labels = last7.labels || [];
  const values = last7.values || [];

  if (_chartSolicitations) _chartSolicitations.destroy();

  _chartSolicitations = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Solicitações',
        data: values,
        borderColor: '#1a56db',
        backgroundColor: 'rgba(26, 86, 219, 0.08)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: '#1a56db',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointHoverRadius: 6,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            font: { family: 'DM Mono', size: 11 },
          },
          grid: { color: 'rgba(0,0,0,.04)' },
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: 'DM Sans', size: 11 } },
        },
      },
    },
  });
}

// ── Chart: top prestadores bar ────────────────────────────────────────────────
function renderChartTopPrestadores(topPrestadores) {
  const ctx = $('chart_top_prestadores');
  if (!ctx) return;

  const labels = topPrestadores.map((x) => {
    const name = (x.prestador_nome || x.email || '—').trim();
    // Truncate long names
    return name.length > 18 ? name.slice(0, 16) + '…' : name;
  });
  const agendados = topPrestadores.map((x) => x.agendamentos_count ?? 0);
  const concluidos = topPrestadores.map((x) => x.concluido_count ?? 0);

  if (_chartTopPrestadores) _chartTopPrestadores.destroy();

  _chartTopPrestadores = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Agendamentos',
          data: agendados,
          backgroundColor: 'rgba(26, 86, 219, 0.2)',
          borderColor: '#1a56db',
          borderWidth: 1.5,
          borderRadius: 4,
          borderSkipped: false,
        },
        {
          label: 'Concluídos',
          data: concluidos,
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderColor: '#10b981',
          borderWidth: 1.5,
          borderRadius: 4,
          borderSkipped: false,
        },
      ],
    },
    options: {
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { family: 'DM Sans', size: 11 },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            font: { family: 'DM Mono', size: 11 },
          },
          grid: { color: 'rgba(0,0,0,.04)' },
        },
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'DM Sans', size: 11 },
            maxRotation: 0,
          },
        },
      },
    },
  });
}

// ── Ranking table (concluídos) ────────────────────────────────────────────────
function renderRanking(topPrestadores) {
  const tbody = $('ranking_rows');
  if (!tbody) return;

  if (!topPrestadores || topPrestadores.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" style="color:var(--ink-3);font-size:12px;padding:16px 0;">Sem dados</td></tr>';
    return;
  }

  const maxConcluidos = Math.max(...topPrestadores.map((x) => x.concluido_count ?? 0), 1);

  tbody.innerHTML = topPrestadores
    .sort((a, b) => (b.concluido_count ?? 0) - (a.concluido_count ?? 0))
    .map((p, i) => {
      const name = (p.prestador_nome || p.email || '—').trim();
      const done = p.concluido_count ?? 0;
      const pct = Math.round((done / maxConcluidos) * 100);
      return `
        <tr>
          <td class="rank-num">${i + 1}</td>
          <td>
            <div style="font-weight:500;font-size:13px;margin-bottom:5px">${name}</div>
            <div style="display:flex;align-items:center;gap:8px">
              <div class="rank-bar-wrap">
                <div class="rank-bar" style="width:${pct}%"></div>
              </div>
            </div>
          </td>
          <td class="rank-count">
            <span class="rank-done-badge">${done}</span>
          </td>
        </tr>`;
    })
    .join('');
}

// ── Load metrics from API ─────────────────────────────────────────────────────
async function loadMetrics() {
  try {
    const res = await fetch('/admin/api/metrics', { headers: { Accept: 'application/json' } });
    const data = await res.json();

    if (!res.ok || data.erro) {
      console.warn('[dashboard] Erro na API metrics:', data);
      return;
    }

    // Cards — visão geral
    setText('m_user_clients', data.total_clients);
    setText('m_user_providers', data.total_providers);
    setText('m_services_total_today', data.services_requested_today);
    setText('m_services_providers_total_done', data.total_concluidos);

    // Cards — status
    setText('m_services_pending', data.status_counts?.pendente);
    setText('m_services_in_progress', data.status_counts?.em_andamento);
    setText('m_services_done', data.status_counts?.concluido);
    setText('m_services_canceled', data.status_counts?.cancelado);

    // Charts
    renderChartStatus(data.status_counts || {});
    renderChartSolicitations(data.solicitations_last_7 || { labels: [], values: [] });
    renderChartTopPrestadores(data.top_prestadores || []);
    renderRanking(data.top_prestadores || []);

  } catch (err) {
    console.error('[dashboard] Falha ao carregar métricas:', err);
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
function boot() {
  loadMetrics();
  setInterval(loadMetrics, 10_000);
}

document.addEventListener('DOMContentLoaded', boot);