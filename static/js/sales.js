// sales.js – Sales & Products page

const fmt  = v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0});
const fmtN = v => Number(v).toLocaleString('en-US');
const PALETTE = ['#3b82d4','#7c5cd8','#10b981','#f59e0b','#ef4444','#06b6d4'];

const CAT_COLORS = {
  'Electronics':'#3b82d4', 'Clothing':'#7c5cd8', 'Home & Kitchen':'#10b981',
  'Books':'#f59e0b', 'Sports & Fitness':'#ef4444'
};

function renderCategoryCards(data) {
  const div = document.getElementById('categoryCards');
  div.innerHTML = data.map(c=>`
    <div class="kpi-card bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
      <div class="text-xs font-medium text-gray-500 uppercase mb-2 truncate">${c.category}</div>
      <div class="text-xl font-bold text-gray-800">${fmt(c.revenue)}</div>
      <div class="text-xs text-gray-400 mt-1">${fmtN(c.orders)} orders · ${Number(c.profit_margin).toFixed(1)}% margin</div>
    </div>`).join('');
}

function buildCatRevenueChart(data) {
  const ctx = document.getElementById('catRevenueChart').getContext('2d');
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: data.map(d=>d.category),
      datasets:[
        { label:'Revenue', data:data.map(d=>d.revenue), backgroundColor:data.map(d=>CAT_COLORS[d.category]||'#3b82d4'), borderRadius:4 },
        { label:'Profit',  data:data.map(d=>d.profit),  backgroundColor:data.map(d=>(CAT_COLORS[d.category]||'#3b82d4')+'80'), borderRadius:4 },
      ]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top', labels:{font:{size:11}} } },
      scales:{ y:{ ticks:{ callback:v=>'$'+Number(v/1000).toFixed(0)+'k' } } } }
  });
}

function buildCatMarginChart(data) {
  const ctx = document.getElementById('catMarginChart').getContext('2d');
  new Chart(ctx, {
    type:'bar',
    data:{
      labels: data.map(d=>d.category),
      datasets:[{ label:'Profit Margin %', data:data.map(d=>d.profit_margin),
        backgroundColor:'#10b981', borderRadius:4 }]
    },
    options:{ responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{ legend:{ display:false } },
      scales:{ x:{ ticks:{ callback:v=>v+'%' }, min:0, max:100 } } }
  });
}

function buildSalesTrendChart(data) {
  const ctx = document.getElementById('salesTrendChart').getContext('2d');
  new Chart(ctx, {
    type:'line',
    data:{
      labels: data.map(d=>d.year_month),
      datasets:[
        { label:'Revenue', data:data.map(d=>d.revenue), borderColor:'#3b82d4', backgroundColor:'rgba(59,130,212,0.08)', fill:true, tension:0.3, pointRadius:2 },
        { label:'Orders',  data:data.map(d=>d.orders),  borderColor:'#f59e0b', borderDash:[5,3], fill:false, tension:0.3, pointRadius:2, yAxisID:'y1' },
      ]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ position:'top', labels:{font:{size:11}} } },
      scales:{
        y:  { ticks:{ callback:v=>'$'+Number(v/1000).toFixed(0)+'k' } },
        y1: { position:'right', grid:{drawOnChartArea:false}, ticks:{font:{size:10}} }
      } }
  });
}

function renderCatTable(data) {
  const tbody = document.getElementById('catTableBody');
  tbody.innerHTML = data.map(c=>`
    <tr class="border-b border-gray-50">
      <td class="py-2 px-3 font-medium">${c.category}</td>
      <td class="py-2 px-3 text-right">${fmtN(c.orders)}</td>
      <td class="py-2 px-3 text-right">${fmtN(c.quantity_sold)}</td>
      <td class="py-2 px-3 text-right font-semibold text-blue-700">${fmt(c.revenue)}</td>
      <td class="py-2 px-3 text-right text-green-700">${fmt(c.profit)}</td>
      <td class="py-2 px-3 text-right">${Number(c.profit_margin).toFixed(1)}%</td>
    </tr>`).join('');
}

function renderTopProds(data) {
  const tbody = document.getElementById('topProdsBody');
  tbody.innerHTML = data.map((p,i)=>`
    <tr class="border-b border-gray-50">
      <td class="py-2 px-3 text-gray-500">${i+1}</td>
      <td class="py-2 px-3 font-medium">${p.product_name}</td>
      <td class="py-2 px-3 text-gray-500">${p.category}</td>
      <td class="py-2 px-3 text-right font-semibold text-blue-700">${fmt(p.revenue)}</td>
      <td class="py-2 px-3 text-right text-green-700">${fmt(p.profit)}</td>
      <td class="py-2 px-3 text-right">${fmtN(p.units_sold)}</td>
      <td class="py-2 px-3 text-right">${fmtN(p.orders)}</td>
    </tr>`).join('');
}

(async () => {
  try {
    const [cats, trend, tops] = await Promise.all([
      fetch('/api/category-performance').then(r=>r.json()),
      fetch('/api/sales-trend').then(r=>r.json()),
      fetch('/api/top-products').then(r=>r.json()),
    ]);
    renderCategoryCards(cats);
    buildCatRevenueChart(cats);
    buildCatMarginChart(cats);
    buildSalesTrendChart(trend);
    renderCatTable(cats);
    renderTopProds(tops);
  } catch(e) {
    console.error('Sales page load error:', e);
    document.getElementById('categoryCards').innerHTML =
      '<div class="col-span-5 text-center text-red-500 py-6">Failed to load data. Please refresh.</div>';
  }
})();
