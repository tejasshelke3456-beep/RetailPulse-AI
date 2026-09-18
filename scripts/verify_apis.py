"""Quick API verification script"""
import sys, os, json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
import app as flask_app

flask_app.app.config['TESTING'] = True
c = flask_app.app.test_client()

GET_APIS = [
    '/api/health',
    '/api/kpis',
    '/api/sales-trend',
    '/api/category-performance',
    '/api/top-products',
    '/api/customer-segments',
    '/api/regional-performance',
    '/api/risk-analysis',
    '/api/opportunities',
    '/api/customer/CUST-0001',
    '/api/insights',
    '/api/churn-summary',
]

print("=" * 55)
print("API VERIFICATION")
print("=" * 55)
passed = 0
for path in GET_APIS:
    r = c.get(path)
    ok = r.status_code == 200
    passed += int(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {r.status_code}  {path}")

# POST predict
payload = {
    "historical_recency":   90,
    "historical_frequency": 5,
    "historical_monetary":  500.0,
    "total_items":          10,
    "average_order_value":  100.0,
    "average_discount":     0.10,
    "age":                  35,
    "region":               "North",
    "gender":               "Male",
}
r = c.post('/api/predict-churn', data=json.dumps(payload), content_type='application/json')
d = json.loads(r.data)
ok = r.status_code == 200 and 'churn_probability' in d
passed += int(ok)
print(f"{'PASS' if ok else 'FAIL'}  {r.status_code}  /api/predict-churn  prob={d.get('churn_probability')}  risk={d.get('risk_level')}")

# 404 test
r404 = c.get('/api/customer/CUST-99999')
ok = r404.status_code == 404
passed += int(ok)
print(f"{'PASS' if ok else 'FAIL'}  {r404.status_code}  /api/customer/CUST-99999 (expect 404)")

# 400 test
rbad = c.post('/api/predict-churn', data='not json', content_type='text/plain')
ok = rbad.status_code == 400
passed += int(ok)
print(f"{'PASS' if ok else 'FAIL'}  {rbad.status_code}  /api/predict-churn bad payload (expect 400)")

print()
print(f"Results: {passed}/15 PASS")

# KPI summary
r = c.get('/api/kpis')
kpis = json.loads(r.data)
print()
print("KPI SUMMARY")
print(f"  Total Revenue   : ${kpis['total_revenue']:>12,.2f}")
print(f"  Total Profit    : ${kpis['total_profit']:>12,.2f}")
print(f"  Avg Order Value : ${kpis['avg_order_value']:>12,.2f}")
print(f"  Total Customers : {kpis['total_customers']:>12,}")
print(f"  Total Orders    : {kpis['total_orders']:>12,}")
print(f"  Profit Margin   : {kpis['avg_profit_margin']:>11.2f}%")
print(f"  Churn Rate      : {kpis['churn_rate']:>11.2f}%")
print(f"  Retention Rate  : {kpis['retention_rate']:>11.2f}%")
