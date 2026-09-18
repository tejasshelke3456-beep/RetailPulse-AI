// dashboard.js – Overview page (index.html)

const PALETTE = ['#3b82d4','#7c5cd8','#10b981','#f59e0b','#ef4444','#06b6d4'];

const fmt   = v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0});
const fmtP  = v => Number(v).toFixed(1) + '%';
const fmtN  = v => Number(v).toLocaleString('en-US');

function renderKpiCards(data) {
  const cards = [
    { label:'Total Revenue',     value: fmt(data.total_revenue),     icon:'fa-dollar-sign',     color:'text-blue-500',   bg:'bg-blue-50' },
    { label:'Total Profit',      value: fmt(data.total_profit),      icon:'fa-chart-line',      color:'text-green-500',  bg:'bg-green-50' },
    { label:'Avg Order Value',   value: fmt(data.avg_order_value),   icon:'fa-shopping-cart',   color:'text-purple-500', bg:'bg-purple-50' },
    { label:'Total Orders',      value: fmtN(data.total_orders),     icon:'fa-box',             color:'text-orange-500', bg:'bg-orange-50' },
    { label:'Total Customers',   value: fmtN(data.total_customers),  icon:'fa-users',           color:'text-cyan-500',   bg:'bg-cyan-50' },
    { label:'Profit Margin',     value: fmtP(data.avg_profit_margin),icon:'fa-percentage',      color:'text-teal-500',   bg:'bg-teal-50' },
    { label:'Churn Rate',        value: fmtP(data.churn_rate),       icon:'fa-user-minus',      color:'text-red-500',    bg:'bg-red-50' },
    { label:'Retention Rate',    value: fmtP(data.retention_rate),   icon:'fa-heart',           color:'text-pink-500',   bg:'bg-pink-50' },
  ];

  const grid = document.getElementById('kpiGrid');
  grid.innerHTML = cards.map(c => `
    <div class="kpi-card bg-white rounded-xl p-5 border border-gray-100 shadow-sm cursor-default">
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">${c.label}</span>
        <div class="w-8 h-8 ${c.bg} ${c.color} rounded-lg flex items-center justify-center text-sm">
          <i class="fas ${c.icon}"></i>
        </div>
      </div>
      <div class="text-2xl font-bold text-gray-800">${c.value}</div>
    </div>
  `).join('');
}

function buildRevenueTrend(data) {
  const ctx = document.getElementById('revenueTrendChart').getContext('2d');
  new Chart(ctx, {
    type:'line',
    data:{
      labels: data.map(d=>d.year_month),
      datasets:[
        { label:'Revenue', data:data.map(d=>d.revenue), borderColor:'#3b82d4', backgroundColor:'rgba(59,130,212,0.08)',
          fill:true, tension:0.3, pointRadius:2 },
        { label:'Profit',  data:data.map(d=>d.profit),  borderColor:'#10b981', backgroundColor:'rgba(16,185,129,0.06)',
          fill:true, tension:0.3, pointRadius:2 },
      ]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top', labels:{ font:{size:11} } } },
      scales:{ x:{ ticks:{ maxRotation:45, font:{size:10} } }, y:{ ticks:{ callback:v=>'$'+Number(v/1000).toFixed(0)+'k' } } } }
  });
}

function buildSegmentDonut(data) {
  const ctx = document.getElementById('segmentDonut').getContext('2d');
  new Chart(ctx, {
    type:'doughnut',
    data:{
      labels: data.map(d=>d.segment),
      datasets:[{ data:data.map(d=>d.count), backgroundColor:PALETTE, borderWidth:2 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ display:false } } }
  });

  const leg = document.getElementById('segmentLegend');
  if (leg) {
    leg.innerHTML = data.map((d,i)=>`
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${PALETTE[i%PALETTE.length]}"></span>
          <span class="text-gray-600">${d.segment}</span>
        </div>
        <span class="font-medium text-gray-700">${d.percentage}%</span>
      </div>`).join('');
  }
}

function buildCategoryChart(data) {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: data.map(d=>d.category),
      datasets:[{ label:'Revenue', data:data.map(d=>d.revenue),
        backgroundColor:PALETTE, borderRadius:4 }]
    },
    options:{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:{ callback:v=>'$'+Number(v/1000).toFixed(0)+'k' } } } }
  });
}

function buildRegionalChart(data) {
  const ctx = document.getElementById('regionalChart').getContext('2d');
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: data.map(d=>d.region),
      datasets:[{ label:'Revenue', data:data.map(d=>d.revenue), backgroundColor:'#3b82d4', borderRadius:4 },
                { label:'Profit',  data:data.map(d=>d.profit),  backgroundColor:'#10b981', borderRadius:4 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top', labels:{ font:{size:11} } } },
      scales:{ y:{ ticks:{ callback:v=>'$'+Number(v/1000).toFixed(0)+'k' } } } }
  });
}

function renderTopProducts(data) {
  const tbody = document.getElementById('topProductsBody');
  if (!data.length) { tbody.innerHTML='<tr><td colspan="6" class="py-6 text-center text-gray-400">No data</td></tr>'; return; }
  tbody.innerHTML = data.map((p,i)=>`
    <tr class="border-b border-gray-50">
      <td class="py-2 px-3 text-gray-500">${i+1}</td>
      <td class="py-2 px-3 font-medium">${p.product_name}</td>
      <td class="py-2 px-3 text-gray-500">${p.category}</td>
      <td class="py-2 px-3 text-right font-semibold text-blue-700">${fmt(p.revenue)}</td>
      <td class="py-2 px-3 text-right text-green-700">${fmt(p.profit)}</td>
      <td class="py-2 px-3 text-right">${fmtN(p.units_sold)}</td>
    </tr>`).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────
(async () => {
  try {
    const [kpis, trend, cats, segs, regional, tops] = await Promise.all([
      fetch('/api/kpis').then(r=>r.json()),
      fetch('/api/sales-trend').then(r=>r.json()),
      fetch('/api/category-performance').then(r=>r.json()),
      fetch('/api/customer-segments').then(r=>r.json()),
      fetch('/api/regional-performance').then(r=>r.json()),
      fetch('/api/top-products').then(r=>r.json()),
    ]);
    renderKpiCards(kpis);
    buildRevenueTrend(trend);
    buildSegmentDonut(segs);
    buildCategoryChart(cats);
    buildRegionalChart(regional);
    renderTopProducts(tops);
  } catch(e) {
    console.error('Dashboard load error:', e);
    document.getElementById('kpiGrid').innerHTML =
      '<div class="col-span-4 text-center text-red-500 py-6">Failed to load data. Please refresh.</div>';
  }
})();
