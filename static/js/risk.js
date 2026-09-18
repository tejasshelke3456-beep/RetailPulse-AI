// risk.js – Risk & Opportunities page

const fmt  = v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0});
const fmtN = v => Number(v).toLocaleString('en-US');

const TREND_ICONS = { up:'fa-arrow-trend-up', down:'fa-arrow-trend-down', neutral:'fa-minus' };
const TREND_COLORS= { up:'text-green-500', down:'text-red-500', neutral:'text-gray-400' };
const PRI_COLORS  = { High:'bg-red-100 text-red-700', Medium:'bg-yellow-100 text-yellow-700', Low:'bg-green-100 text-green-700' };

let _insights = [];
let _recs     = [];

function renderRiskSummary(data) {
  const ch = data.churn_summary;
  const cards = [
    { label:'Total Customers',  value:fmtN(ch.total_customers),  icon:'fa-users',       color:'text-blue-500',  bg:'bg-blue-50' },
    { label:'Churned',          value:fmtN(ch.churned),           icon:'fa-user-minus',  color:'text-red-500',   bg:'bg-red-50' },
    { label:'Retained',         value:fmtN(ch.retained),          icon:'fa-user-check',  color:'text-green-500', bg:'bg-green-50' },
    { label:'Churn Rate',       value:Number(ch.churn_rate).toFixed(2)+'%', icon:'fa-percentage', color:'text-orange-500', bg:'bg-orange-50' },
  ];
  document.getElementById('riskSummaryRow').innerHTML = cards.map(c=>`
    <div class="kpi-card bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-gray-500 uppercase">${c.label}</span>
        <div class="w-7 h-7 ${c.bg} ${c.color} rounded-lg flex items-center justify-center text-xs">
          <i class="fas ${c.icon}"></i>
        </div>
      </div>
      <div class="text-2xl font-bold text-gray-800">${c.value}</div>
    </div>`).join('');
}

function buildChurnPie(data) {
  const ch  = data.churn_summary;
  const ctx = document.getElementById('churnPieChart').getContext('2d');
  new Chart(ctx, {
    type:'doughnut',
    data:{
      labels:['Churned','Retained'],
      datasets:[{ data:[ch.churned, ch.retained], backgroundColor:['#ef4444','#10b981'], borderWidth:2 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'bottom', labels:{font:{size:11}} } } }
  });
}

function buildRiskSegmentChart(data) {
  const seg = data.segments || [];
  const ctx = document.getElementById('riskSegmentChart').getContext('2d');
  const COLORS = ['#3b82d4','#7c5cd8','#10b981','#f59e0b','#ef4444'];
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: seg.map(s=>s.segment),
      datasets:[{ label:'Customers', data:seg.map(s=>s.count),
        backgroundColor:COLORS, borderRadius:4 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ display:false } },
      scales:{ y:{ ticks:{ stepSize:200 } } } }
  });
}

function renderInsights(list) {
  const div = document.getElementById('insightsGrid');
  document.getElementById('insightCount').textContent = list.length + ' insights';
  if (!list.length) {
    div.innerHTML='<div class="col-span-3 text-center text-gray-400 py-6">No insights available.</div>';
    return;
  }
  div.innerHTML = list.map(i=>`
    <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm insight-card"
         data-category="${i.category}">
      <div class="flex items-start justify-between mb-2">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">${i.category}</span>
        <i class="fas ${TREND_ICONS[i.trend]||'fa-minus'} text-sm ${TREND_COLORS[i.trend]||'text-gray-400'}"></i>
      </div>
      <div class="font-semibold text-gray-800 mb-1 text-sm">${i.title}</div>
      <div class="text-xs text-gray-500 mb-2 leading-relaxed">${i.description}</div>
      <div class="text-lg font-bold text-blue-700">${i.value}</div>
    </div>`).join('');
}

function renderRecs(list) {
  const div = document.getElementById('recsGrid');
  document.getElementById('recCount').textContent = list.length + ' recommendations';
  if (!list.length) {
    div.innerHTML='<div class="col-span-3 text-center text-gray-400 py-6">No recommendations available.</div>';
    return;
  }
  div.innerHTML = list.map(r=>`
    <div class="bg-white rounded-xl p-4 border border-gray-100 shadow-sm rec-card"
         data-priority="${r.priority}" data-category="${r.category}">
      <div class="flex items-start justify-between mb-2">
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${PRI_COLORS[r.priority]||'bg-gray-100 text-gray-600'}">${r.priority} Priority</span>
        <span class="text-xs text-gray-400">${r.category}</span>
      </div>
      <div class="font-semibold text-gray-800 mb-1 text-sm">${r.title}</div>
      <div class="text-xs text-gray-500 mb-2 leading-relaxed">${r.description}</div>
      <div class="text-xs font-medium text-green-700 flex items-center gap-1">
        <i class="fas fa-bolt"></i> ${r.impact}
      </div>
    </div>`).join('');
}

function filterInsights() {
  const cat = document.getElementById('insightCategoryFilter').value;
  document.querySelectorAll('.insight-card').forEach(el => {
    el.style.display = (!cat || el.dataset.category === cat) ? '' : 'none';
  });
}

function filterRecs() {
  const pri = document.getElementById('priorityFilter').value;
  document.querySelectorAll('.rec-card').forEach(el => {
    el.style.display = (!pri || el.dataset.priority === pri) ? '' : 'none';
  });
}

function resetFilters() {
  document.getElementById('insightCategoryFilter').value = '';
  document.getElementById('priorityFilter').value = '';
  filterInsights();
  filterRecs();
}

(async () => {
  try {
    const [risk, insights, recs] = await Promise.all([
      fetch('/api/risk-analysis').then(r=>r.json()),
      fetch('/api/insights').then(r=>r.json()),
      fetch('/api/opportunities').then(r=>r.json()),
    ]);
    renderRiskSummary(risk);
    buildChurnPie(risk);
    buildRiskSegmentChart(risk);
    _insights = insights;
    _recs     = recs;
    renderInsights(insights);
    renderRecs(recs);
  } catch(e) {
    console.error('Risk page error:', e);
    document.getElementById('riskSummaryRow').innerHTML =
      '<div class="col-span-4 text-center text-red-500 py-6">Failed to load data.</div>';
  }
})();
