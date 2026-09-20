from decimal import Decimal
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pricing.artifacts import ArtifactCatalog
from pricing.engine import candidate_prices, simulate
from pricing.schemas import SimulationRequest
from pricing.api import create_app

@pytest.fixture(scope='module')
def catalog():
    return ArtifactCatalog()

@pytest.fixture
def payload(catalog):
    return {'product_id':next(iter(catalog.products)),'current_price':100,'stock':100,'demand_source':'manual','base_demand':10}

@pytest.fixture
def client(catalog,tmp_path):
    with TestClient(create_app(catalog,tmp_path/'test.sqlite')) as c:yield c

def test_hybrid_equations_and_grid(catalog,payload):
    r=simulate(SimulationRequest(**payload),catalog)
    assert [s.price for s in r.scenarios]==[90,95,100,105,110]
    current=next(s for s in r.scenarios if s.price==100)
    assert current.response_factor==1 and current.adjusted_demand==10 and current.estimated_revenue==1000
    for s in r.scenarios:
        assert s.response_factor==pytest.approx((s.price/100)**catalog.beta)
        assert s.adjusted_demand==pytest.approx(10*s.response_factor)
        assert s.sellable_units<=100
        assert s.estimated_revenue==pytest.approx(round(s.price*s.sellable_units,2))
    assert r.recommended_price==90

def test_limited_stock_changes_optimum(catalog,payload):
    payload['stock']=2
    r=simulate(SimulationRequest(**payload),catalog)
    assert r.recommended_price==110 and r.sellable_units==2 and r.recommended_estimated_revenue==220

@pytest.mark.parametrize('override',[{'stock':0},{'base_demand':0}])
def test_zero_preserves_current_price(catalog,payload,override):
    r=simulate(SimulationRequest(**(payload|override)),catalog)
    assert r.recommended_price==100 and r.recommended_estimated_revenue==0
    assert r.estimated_revenue_change_pct is None

@pytest.mark.parametrize('price',[Decimal('.01'),Decimal('.03'),Decimal('1.01'),Decimal('99.99')])
def test_rounding_keeps_prices_inside_limits(payload,price):
    req=SimulationRequest(**(payload|{'current_price':price,'step_pct':.1,'max_decrease_pct':3,'max_increase_pct':7}))
    values=candidate_prices(req)
    assert price in values and len(values)==len(set(values))
    assert all(v>0 and price*Decimal('.97')<=v<=price*Decimal('1.07') for v in values)

def test_no_change_bounds(catalog,payload):
    r=simulate(SimulationRequest(**(payload|{'max_decrease_pct':0,'max_increase_pct':0})),catalog)
    assert len(r.scenarios)==1 and r.recommended_price==100

def test_support_and_extrapolation_are_visible(catalog,payload):
    pid=next(pid for pid,p in catalog.products.items() if not p['sufficient_individual_support'])
    r=simulate(SimulationRequest(**(payload|{'product_id':pid,'current_price':1000000})),catalog)
    assert not r.sufficient_individual_support
    assert all(s.outside_historical_range and s.warnings for s in r.scenarios)
    assert any('insuficiente' in w for w in r.warnings)
    assert any('recomendado está fora' in w for w in r.warnings)

def test_moving_average_uses_frozen_snapshot(catalog,payload):
    req=SimulationRequest(**{k:v for k,v in (payload|{'demand_source':'moving_average4'}).items() if k!='base_demand'})
    r=simulate(req,catalog)
    expected=catalog.get_snapshot(req.product_id)
    assert r.base_demand==expected['base_demand']
    assert r.demand_reference_week==expected['week']
    assert r.artifact_versions['demand_model']=='MovingAverage4'

@pytest.mark.parametrize('change',[{'current_price':0},{'current_price':-10},{'stock':-1},{'stock':1.5},{'stock':True},{'base_demand':-1},{'base_demand':float('nan')},{'base_demand':float('inf')},{'max_increase_pct':11},{'max_decrease_pct':-1},{'step_pct':0},{'current_price':1.001},{'demand_source':'unknown'}])
def test_invalid_input(payload,change):
    with pytest.raises(ValidationError):SimulationRequest(**(payload|change))

def test_api_lifecycle_and_persistence(client,payload):
    assert client.get('/health').json()['status']=='ok'
    assert len(client.get('/api/v1/products').json())==136
    assert client.get('/api/v1/metadata').json()['experimental']
    r=client.post('/api/v1/simulations',json=payload)
    assert r.status_code==201, r.text
    saved=r.json()
    assert len(saved['scenarios'])==5
    assert saved['artifact_versions']['demand_model']=='MovingAverage4'
    detail=client.get('/api/v1/simulations/'+saved['id'])
    assert detail.json()['result']==saved
    assert client.get('/api/v1/simulations').json()[0]['id']==saved['id']
    assert client.get('/api/v1/simulations?limit=101').status_code==422
    assert client.get('/api/v1/simulations/nonexistent').status_code==404

@pytest.mark.parametrize('change',[{'current_price':0},{'stock':-1},{'base_demand':None},{'max_increase_pct':20},{'stock':1.5}])
def test_api_rejects_invalid(client,payload,change):
    assert client.post('/api/v1/simulations',json=payload|change).status_code==422

def test_unknown_product_and_week(client,payload):
    assert client.post('/api/v1/simulations',json=payload|{'product_id':'unknown'}).status_code==404
    req={k:v for k,v in payload.items() if k!='base_demand'}
    req.update(demand_source='moving_average4',reference_week='2026-01-01')
    assert client.post('/api/v1/simulations',json=req).status_code==422
    assert client.get('/api/v1/products/unknown/history').status_code==404

def test_store_survives_restart(catalog,tmp_path,payload):
    db=tmp_path/'persistent.sqlite'
    with TestClient(create_app(catalog,db)) as c:
        sid=c.post('/api/v1/simulations',json=payload).json()['id']
    with TestClient(create_app(catalog,db)) as c:
        assert c.get('/api/v1/simulations/'+sid).status_code==200

def test_fractional_cent_boundary_is_kept_conservatively(payload):
    req=SimulationRequest(**(payload|{'current_price':119.99}))
    values=candidate_prices(req)
    assert values[0]==Decimal('108.00')
    assert values[-1]==Decimal('131.98')

@pytest.mark.parametrize('operation,path', [('list','/api/v1/simulations'), ('get','/api/v1/simulations/example')])
def test_history_database_failure_is_explicit(client,monkeypatch,operation,path):
    import sqlite3
    def fail(*args):
        raise sqlite3.OperationalError('database unavailable')
    monkeypatch.setattr(client.app.state.store,operation,fail)
    response=client.get(path)
    assert response.status_code==503
    assert 'consultar' in response.json()['detail']


def test_failed_save_is_not_reported_as_success(client,payload,monkeypatch):
    import sqlite3
    def fail(*args):
        raise sqlite3.OperationalError('database unavailable')
    monkeypatch.setattr(client.app.state.store,'save',fail)
    assert client.post('/api/v1/simulations',json=payload).status_code==503
    assert client.get('/api/v1/simulations').json()==[]
