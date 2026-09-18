// prediction.js – AI Churn Prediction page

const fmt  = v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits:0, maximumFractionDigits:0});
const fmtN = v => Number(v).toLocaleString('en-US');

function renderChurnOverview(data) {
  const cards = [
    { label:'Total Customers',  value:fmtN(data.total_customers), icon:'fa-users',      color:'text-blue-500',  bg:'bg-blue-50' },
    { label:'Churned',          value:fmtN(data.churned),          icon:'fa-user-minus', color:'text-red-500',   bg:'bg-red-50' },
    { label:'Retained',         value:fmtN(data.retained),         icon:'fa-user-check', color:'text-green-500', bg:'bg-green-50' },
    { label:'Churn Rate',       value:Number(data.churn_rate).toFixed(2)+'%', icon:'fa-percentage', color:'text-orange-500', bg:'bg-orange-50' },
  ];
  document.getElementById('churnOverviewRow').innerHTML = cards.map(c=>`
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

function renderModelMetrics(data) {
  const div = document.getElementById('modelMetricsGrid');
  const metrics = [
    { label:'Random Forest F1',    value:Number(data.rf_f1_score).toFixed(4),  color:'text-blue-600' },
    { label:'Random Forest AUC',   value:Number(data.rf_roc_auc).toFixed(4),   color:'text-blue-600' },
    { label:'Logistic Reg. F1',    value:Number(data.lr_f1_score).toFixed(4),  color:'text-gray-600' },
    { label:'Logistic Reg. AUC',   value:Number(data.lr_roc_auc).toFixed(4),   color:'text-gray-600' },
  ];
  div.innerHTML = metrics.map(m=>`
    <div class="bg-gray-50 rounded-lg p-3 text-center">
      <div class="text-xs text-gray-500 mb-1">${m.label}</div>
      <div class="text-xl font-bold ${m.color}">${m.value}</div>
    </div>`).join('');
}

function buildChurnDonut(data) {
  const ctx = document.getElementById('churnDonut').getContext('2d');
  new Chart(ctx, {
    type:'doughnut',
    data:{
      labels:['Churned','Retained'],
      datasets:[{
        data:[data.churned, data.retained],
        backgroundColor:['#ef4444','#10b981'],
        borderWidth:2
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{ position:'bottom', labels:{font:{size:12}} },
        tooltip:{
          callbacks:{
            label: ctx => ` ${ctx.label}: ${fmtN(ctx.raw)} (${(ctx.raw/(data.churned+data.retained)*100).toFixed(1)}%)`
          }
        }
      }
    }
  });
}

async function submitPrediction(e) {
  e.preventDefault();
  const resDiv = document.getElementById('predResult');
  resDiv.classList.remove('hidden');
  resDiv.innerHTML = '<div class="flex items-center gap-2 text-gray-500 text-sm"><div class="spinner"></div> Running prediction…</div>';

  const payload = {
    historical_recency:    parseFloat(document.getElementById('f_recency').value),
    historical_frequency:  parseFloat(document.getElementById('f_frequency').value),
    historical_monetary:   parseFloat(document.getElementById('f_monetary').value),
    total_items:           parseFloat(document.getElementById('f_items').value),
    average_order_value:   parseFloat(document.getElementById('f_aov').value),
    average_discount:      parseFloat(document.getElementById('f_disc').value),
    age:                   parseFloat(document.getElementById('f_age').value),
    region:                document.getElementById('f_region').value,
    gender:                document.getElementById('f_gender').value,
  };

  try {
    const resp = await fetch('/api/predict-churn', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });

    const data = await resp.json();

    if (!resp.ok) {
      resDiv.innerHTML = `
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          <i class="fas fa-exclamation-circle mr-1"></i> ${data.error || 'Prediction failed.'}
        </div>`;
      return;
    }

    const prob    = (data.churn_probability * 100).toFixed(2);
    const pred    = data.prediction;
    const risk    = data.risk_level;
    const riskCfg = {
      High:   { bg:'bg-red-50',    border:'border-red-200',    dot:'bg-red-500',    text:'text-red-700',   label:'High Risk' },
      Medium: { bg:'bg-yellow-50', border:'border-yellow-200', dot:'bg-yellow-500', text:'text-yellow-700',label:'Medium Risk' },
      Low:    { bg:'bg-green-50',  border:'border-green-200',  dot:'bg-green-500',  text:'text-green-700', label:'Low Risk' },
    };
    const c = riskCfg[risk] || riskCfg.Medium;

    resDiv.innerHTML = `
      <div class="${c.bg} border ${c.border} rounded-xl p-5">
        <div class="flex items-center gap-3 mb-3">
          <span class="w-3 h-3 rounded-full ${c.dot}"></span>
          <span class="font-bold text-lg ${c.text}">${c.label}</span>
        </div>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div class="bg-white rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">Churn Probability</div>
            <div class="text-2xl font-bold ${c.text}">${prob}%</div>
          </div>
          <div class="bg-white rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">Prediction</div>
            <div class="text-xl font-bold ${pred===1?'text-red-600':'text-green-600'}">${pred===1?'Will Churn':'Will Retain'}</div>
          </div>
          <div class="bg-white rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">Risk Level</div>
            <div class="text-xl font-bold ${c.text}">${risk}</div>
          </div>
        </div>
        <p class="text-xs ${c.text} mt-3">
          <i class="fas fa-info-circle mr-1"></i>
          Note: This is a probabilistic prediction based on historical patterns. It does not guarantee future customer behaviour.
        </p>
      </div>`;
  } catch(err) {
    resDiv.innerHTML = `
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
        <i class="fas fa-exclamation-circle mr-1"></i> Network error. Is the server running?
      </div>`;
  }
}

(async () => {
  try {
    const data = await fetch('/api/churn-summary').then(r=>r.json());
    renderChurnOverview(data);
    renderModelMetrics(data);
    buildChurnDonut(data);
  } catch(e) {
    console.error('Prediction page error:', e);
    document.getElementById('churnOverviewRow').innerHTML =
      '<div class="col-span-4 text-center text-red-500 py-6">Failed to load data.</div>';
  }
})();
