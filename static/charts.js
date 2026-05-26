window.onload = function () {

  /* ── Common chart defaults ── */
  Chart.defaults.color = '#4a5568';
  Chart.defaults.font.family = "'IBM Plex Mono', monospace";

  const PALETTE = [
    'rgba(0,229,160,0.75)',   'rgba(74,144,226,0.75)',
    'rgba(240,168,48,0.75)',  'rgba(226,85,85,0.75)',
    'rgba(160,100,240,0.75)', 'rgba(0,180,220,0.75)',
    'rgba(255,140,80,0.75)',  'rgba(80,200,120,0.75)',
  ];
  const PALETTE_BORDER = PALETTE.map(c => c.replace('0.75', '1'));

  const tooltip = {
    backgroundColor: '#1f242c', borderColor: '#2a3040', borderWidth: 1,
    titleColor: '#8a96a8', bodyColor: '#e8edf5', padding: 12,
    titleFont: { family: "'IBM Plex Mono', monospace", size: 11 },
    bodyFont:  { family: "'IBM Plex Mono', monospace", size: 12 },
  };

  const gridColor = '#1f242c';

  /* ── 1. Expense Bar Chart (by vendor / monthly) ── */
  const barCtx = document.getElementById('expenseChart');
  if (barCtx) {
    const labels  = JSON.parse(barCtx.dataset.labels  || '[]');
    const amounts = JSON.parse(barCtx.dataset.amounts || '[]');
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['No Data'],
        datasets: [{
          label: 'Total (₹)',
          data: amounts.length ? amounts : [0],
          backgroundColor: 'rgba(0,229,160,0.18)',
          borderColor:     'rgba(0,229,160,0.8)',
          borderWidth: 1.5, borderRadius: 6, borderSkipped: false,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: { ...tooltip, callbacks: { label: ctx => ' ₹ ' + Number(ctx.parsed.y).toLocaleString('en-IN') } }
        },
        scales: {
          x: { grid: { color: gridColor }, ticks: { maxRotation: 35, maxTicksLimit: 10 } },
          y: { beginAtZero: true, grid: { color: gridColor },
               ticks: { callback: v => '₹' + Number(v).toLocaleString('en-IN') } }
        }
      }
    });
  }

  /* ── 2. Donut: Invoice count by vendor ── */
  const donutCtx = document.getElementById('vendorChart');
  if (donutCtx) {
    const vLabels = JSON.parse(donutCtx.dataset.labels || '[]');
    const vCounts = JSON.parse(donutCtx.dataset.counts || '[]');
    new Chart(donutCtx, {
      type: 'doughnut',
      data: {
        labels: vLabels.length ? vLabels : ['No Data'],
        datasets: [{ data: vCounts.length ? vCounts : [1], backgroundColor: PALETTE, borderColor: '#111418', borderWidth: 3, hoverOffset: 6 }]
      },
      options: {
        responsive: true, cutout: '68%',
        plugins: {
          legend: { position: 'right', labels: { color: '#8a96a8', padding: 14, boxWidth: 10, boxHeight: 10 } },
          tooltip
        }
      }
    });
  }

  /* ── 3. Monthly spend line chart ── */
  const monthCtx = document.getElementById('monthlyChart');
  if (monthCtx) {
    const mLabels  = JSON.parse(monthCtx.dataset.labels  || '[]');
    const mAmounts = JSON.parse(monthCtx.dataset.amounts || '[]');
    new Chart(monthCtx, {
      type: 'line',
      data: {
        labels: mLabels.length ? mLabels : ['No Data'],
        datasets: [{
          label: 'Monthly Spend (₹)',
          data: mAmounts.length ? mAmounts : [0],
          borderColor: 'rgba(0,229,160,0.9)', backgroundColor: 'rgba(0,229,160,0.06)',
          borderWidth: 2, pointBackgroundColor: 'var(--accent)',
          pointRadius: 4, fill: true, tension: 0.35,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: { ...tooltip, callbacks: { label: ctx => ' ₹ ' + Number(ctx.parsed.y).toLocaleString('en-IN') } } },
        scales: {
          x: { grid: { color: gridColor } },
          y: { beginAtZero: true, grid: { color: gridColor }, ticks: { callback: v => '₹' + Number(v).toLocaleString('en-IN') } }
        }
      }
    });
  }

  /* ── 4. Category pie chart ── */
  const catCtx = document.getElementById('categoryChart');
  if (catCtx) {
    const cLabels  = JSON.parse(catCtx.dataset.labels  || '[]');
    const cAmounts = JSON.parse(catCtx.dataset.amounts || '[]');
    new Chart(catCtx, {
      type: 'pie',
      data: {
        labels: cLabels.length ? cLabels : ['No Data'],
        datasets: [{ data: cAmounts.length ? cAmounts : [1], backgroundColor: PALETTE, borderColor: '#111418', borderWidth: 2 }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'right', labels: { color: '#8a96a8', padding: 12, boxWidth: 10 } },
          tooltip: { ...tooltip, callbacks: { label: ctx => ' ₹ ' + Number(ctx.parsed).toLocaleString('en-IN') } }
        }
      }
    });
  }

  /* ── 5. GST horizontal bar ── */
  const gstCtx = document.getElementById('gstChart');
  if (gstCtx) {
    const gLabels = JSON.parse(gstCtx.dataset.labels || '[]');
    const gAmts   = JSON.parse(gstCtx.dataset.amounts || '[]');
    new Chart(gstCtx, {
      type: 'bar',
      data: {
        labels: gLabels.length ? gLabels : ['No Data'],
        datasets: [{
          label: 'GST (₹)', data: gAmts.length ? gAmts : [0],
          backgroundColor: 'rgba(240,168,48,0.2)', borderColor: 'rgba(240,168,48,0.8)',
          borderWidth: 1.5, borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y', responsive: true,
        plugins: { legend: { display: false }, tooltip },
        scales: {
          x: { beginAtZero: true, grid: { color: gridColor }, ticks: { callback: v => '₹' + Number(v).toLocaleString('en-IN') } },
          y: { grid: { display: false } }
        }
      }
    });
  }

  /* ── Drag-and-drop on index ── */
  const zone = document.querySelector('.upload-zone');
  if (zone) {
    ['dragenter','dragover'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add('drag-over'); }));
    ['dragleave','drop'].forEach(e => zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.remove('drag-over'); }));
    zone.addEventListener('drop', ev => {
      const file = ev.dataTransfer.files[0];
      if (file) {
        const input = zone.querySelector('input[type="file"]');
        const dt = new DataTransfer(); dt.items.add(file); input.files = dt.files;
        zone.querySelector('.upload-title').textContent = file.name;
        zone.querySelector('.upload-sub').textContent = (file.size / 1024).toFixed(1) + ' KB · ready to process';
      }
    });
    const input = zone.querySelector('input[type="file"]');
    if (input) input.addEventListener('change', () => {
      const file = input.files[0];
      if (file) {
        zone.querySelector('.upload-title').textContent = file.name;
        zone.querySelector('.upload-sub').textContent = (file.size / 1024).toFixed(1) + ' KB · ready to process';
      }
    });
  }

  /* ── Invoice type card selection ── */
  document.querySelectorAll('.type-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.type-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      card.querySelector('input[type=radio]').checked = true;
    });
  });
};