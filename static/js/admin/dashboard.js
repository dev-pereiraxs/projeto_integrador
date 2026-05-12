/* Dashboard Admin — Agenda Fácil */

const el = (id) => document.getElementById(id);

let chartStatus = null;
let chartSolicitations = null;

function setText(id, value) {
  const node = el(id);
  if (!node) return;
  node.textContent = value ?? 0;
}

function renderCharts(metrics) {
  // Status pie/doughnut
  const status = metrics.status_counts || {};
  const labels = ['pendente', 'em_andamento', 'concluido', 'cancelado'];
  const data = labels.map((k) => status[k] ?? 0);

  const colors = ['#fde68a', '#93c5fd', '#86efac', '#fca5a5'];

  const ctx1 = document.getElementById('chart_status');
  if (ctx1) {
    if (chartStatus) chartStatus.destroy();
    chartStatus = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 0,
        }]
      },
      options: {
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // Solicitations line
  const daily = metrics.solicitations_last_7 || { labels: [], values: [] };
  const ctx2 = document.getElementById('chart_solicitations');
  if (ctx2) {
    if (chartSolicitations) chartSolicitations.destroy();
    chartSolicitations = new Chart(ctx2, {
      type: 'line',
      data: {
        labels: daily.labels || [],
        datasets: [{
          label: 'Solicitações',
          data: daily.values || [],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, .12)',
          tension: 0.35,
          fill: true,
          pointRadius: 3
        }]
      },
      options: {
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
}

async function loadMetrics() {
  try {
    const res = await fetch('/admin/api/metrics', { headers: { 'Accept': 'application/json' } });
    const data = await res.json();
    if (!res.ok || data.erro) {
      console.warn('Erro metrics:', data);
      return;
    }

    // Cards
    setText('m_user_clients', data.total_clients);
    setText('m_user_providers', data.total_providers);
    setText('m_services_total_today', data.services_requested_today);

    setText('m_services_pending', data.status_counts?.pendente);
    setText('m_services_in_progress', data.status_counts?.em_andamento);
    setText('m_services_done', data.status_counts?.concluido);

    renderCharts(data);
  } catch (e) {
    // silêncio
  }
}

function boot() {
  loadMetrics();
  setInterval(loadMetrics, 10000);
}

document.addEventListener('DOMContentLoaded', boot);

