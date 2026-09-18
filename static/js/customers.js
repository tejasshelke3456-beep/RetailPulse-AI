// customers.js – Customer Analytics page

const PALETTE = ['#3b82d4','#7c5cd8','#10b981','#f59e0b','#ef4444','#06b6d4'];
const fmt  = v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0});
const fmtN = v => Number(v).toLocaleString('en-US');

const SEG_COLORS = {
  'VIP':'#3b82d4', 'Loyal':'#7c5cd8', 'Potential Loyalist':'#10b981',
  'At Risk':'#f59e0b', 'Hibernating':'#ef4444'
};
const SEG_ICONS = {
  'VIP':'fa-crown', 'Loyal':'fa-star', 'Potential Loyalist':'fa-seedling',
  'At Risk':'fa-exclamation-triangle', 'Hibernating':'fa-moon'
};

function renderSegmentCards(data) {
  const div = document.getElementById('segmentCards');
  div.innerHTML = data.map(s=>{
    const col = SEG_COLORS[s.segment] || '#6b7280';
    const icon = SEG_ICONS[s.segment] || 'fa-users';
    return `
    <div class="kpi-card bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
      <div class="flex items-center gap-2 mb-2">
        <i class="fas ${icon} text-sm" style="color:${col}"></i>
        <span class="text-xs font-medium text-gray-500 uppercase">${s.segment}</span>
      </div>
      <div class="text-2xl font-bold text-gray-800">${fmtN(s.count)}</div>
      <div class="text-xs text-gray-400 mt-1">${s.percentage}% of customers</div>
    </div>`;
  }).join('');
}

function buildSegmentPie(data) {
  const ctx = document.getElementById('segmentPieChart').getContext('2d');
  new Chart(ctx, {
    type:'doughnut',
    data:{
      labels: data.map(d=>d.segment),
      datasets:[{ data:data.map(d=>d.count),
        backgroundColor:data.map(d=>SEG_COLORS[d.segment]||'#6b7280'),
        borderWidth:2 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'bottom', labels:{font:{size:11}} } } }
  });
}

function buildSegmentRevenueChart(data) {
  const ctx = document.getElementById('segmentRevenueChart').getContext('2d');
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: data.map(d=>d.segment),
      datasets:[{ label:'Avg Revenue',
        data:data.map(d=>d.avg_revenue),
        backgroundColor:data.map(d=>SEG_COLORS[d.segment]||'#6b7280'),
        borderRadius:4 }]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ display:false } },
      scales:{ y:{ ticks:{ callback:v=>'$'+Number(v).toFixed(0) } } } }
  });
}

function renderSegmentTable(data) {
  const tbody = document.getElementById('segmentTableBody');
  tbody.innerHTML = data.map(s=>`
    <tr class="border-b border-gray-50">
      <td class="py-2 px-3">
        <span class="inline-flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full" style="background:${SEG_COLORS[s.segment]||'#6b7280'}"></span>
          <span class="font-medium">${s.segment}</span>
        </span>
      </td>
      <td class="py-2 px-3 text-right">${fmtN(s.count)}</td>
      <td class="py-2 px-3 text-right">${s.percentage}%</td>
      <td class="py-2 px-3 text-right font-semibold text-blue-700">${fmt(s.avg_revenue)}</td>
      <td class="py-2 px-3 text-right">${Number(s.avg_recency).toFixed(0)}</td>
      <td class="py-2 px-3 text-right">${Number(s.avg_frequency).toFixed(1)}</td>
      <td class="py-2 px-3 text-right">${fmt(s.avg_monetary)}</td>
    </tr>`).join('');
}

// ── Customer Lookup ───────────────────────────────────────────────────────
async function lookupCustomer() {
  const id  = document.getElementById('customerInput').value.trim().toUpperCase();
  const res = document.getElementById('customerResult');
  const err = document.getElementById('customerError');
  const dat = document.getElementById('customerData');

  res.classList.remove('hidden');
  err.classList.add('hidden');
  dat.classList.add('hidden');

  if (!id) {
    err.textContent = 'Please enter a customer ID (e.g. CUST-0001)';
    err.classList.remove('hidden');
    return;
  }

  try {
    const resp = await fetch(`/api/customer/${encodeURIComponent(id)}`);
    if (resp.status === 404) {
      const j = await resp.json();
      err.textContent = j.error || `Customer '${id}' not found.`;
      err.classList.remove('hidden');
      return;
    }
    if (!resp.ok) {
      err.textContent = 'Unexpected server error. Please try again.';
      err.classList.remove('hidden');
      return;
    }
    const c = await resp.json();
    renderCustomerCard(c);
    dat.classList.remove('hidden');
  } catch(e) {
    err.textContent = 'Network error. Is the server running?';
    err.classList.remove('hidden');
  }
}

function renderCustomerCard(c) {
  const dat  = document.getElementById('customerData');
  const seg  = c.segment || 'Unknown';
  const col  = SEG_COLORS[seg] || '#6b7280';
  const icon = SEG_ICONS[seg]  || 'fa-user';

  const fields = [
    { label:'Customer ID',    value:c.customer_id },
    { label:'Segment',        value:`<span class="font-semibold" style="color:${col}">${seg}</span>` },
    { label:'Region',         value:c.region || '—' },
    { label:'Age',            value:c.age || '—' },
    { label:'Gender',         value:c.gender || '—' },
    { label:'Churn Status',   value: c.is_churned ? '<span class="text-red-600 font-semibold">Churned</span>' : '<span class="text-green-600 font-semibold">Retained</span>' },
    { label:'Total Revenue',  value:fmt(c.total_revenue||0) },
    { label:'Total Orders',   value:fmtN(c.total_orders||0) },
    { label:'Avg Order Value',value:fmt(c.average_order_value||0) },
    { label:'Recency (days)', value:Number(c.historical_recency||0).toFixed(0) },
    { label:'Frequency',      value:fmtN(c.historical_frequency||0) },
    { label:'Monetary',       value:fmt(c.historical_monetary||0) },
    { label:'RFM Scores',     value:`R:${c.r_score} F:${c.f_score} M:${c.m_score}` },
    { label:'RFM Total',      value:c.rfm_score },
    { label:'Avg Discount',   value:(Number(c.average_discount||0)*100).toFixed(1)+'%' },
    { label:'Total Profit',   value:fmt(c.total_profit||0) },
  ];

  dat.querySelector('div').innerHTML = fields.map(f=>`
    <div class="bg-gray-50 rounded-lg p-3">
      <div class="text-xs text-gray-500 mb-0.5">${f.label}</div>
      <div class="text-sm font-medium text-gray-800">${f.value}</div>
    </div>`).join('');
}

// Allow Enter key in search input
document.getElementById('customerInput')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') lookupCustomer();
});

// ── Init ──────────────────────────────────────────────────────────────────
(async () => {
  try {
    const segs = await fetch('/api/customer-segments').then(r=>r.json());
    renderSegmentCards(segs);
    buildSegmentPie(segs);
    buildSegmentRevenueChart(segs);
    renderSegmentTable(segs);
  } catch(e) {
    console.error('Customers page error:', e);
    document.getElementById('segmentCards').innerHTML =
      '<div class="col-span-5 text-center text-red-500 py-6">Failed to load data.</div>';
  }
})();
