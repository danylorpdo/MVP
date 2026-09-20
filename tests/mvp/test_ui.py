from pathlib import Path
import hashlib
import json
import httpx
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from pricing.api import create_app
from pricing.artifacts import ROOT


def test_streamlit_full_flow(monkeypatch,tmp_path):
    with TestClient(create_app(db_path=tmp_path/'ui.sqlite')) as client:
        def route(method,url,**kwargs):
            kwargs.pop('timeout',None)
            return client.request(method,url.replace('http://127.0.0.1:8000',''),**kwargs)
        monkeypatch.setenv('PRICING_API_URL','http://127.0.0.1:8000')
        monkeypatch.setattr(httpx,'request',route)
        at=AppTest.from_file(str(ROOT/'pricing/ui.py'),default_timeout=20).run()
        assert not at.exception
        next(b for b in at.button if b.label=='Comparar preços').click().run()
        assert not at.exception and len(at.metric)==7
        assert at.session_state['result']['demand_source']=='manual'
        next(r for r in at.radio if r.label=='Origem da demanda-base').set_value('MovingAverage4 histórico').run()
        assert not at.exception
        next(b for b in at.button if b.label=='Comparar preços').click().run()
        assert not at.exception
        assert at.session_state['result']['demand_source']=='moving_average4'
        assert at.session_state['result']['demand_reference_week']=='2018-08-20'
        next(r for r in at.radio if r.label=='Navegação').set_value('Histórico').run()
        assert not at.exception and len(at.metric)==7
        assert len(client.get('/api/v1/simulations').json())==2
        next(r for r in at.radio if r.label=='Navegação').set_value('Metodologia').run()
        assert not at.exception
        assert any('Elasticidade' in v.label for v in at.metric)


def test_scientific_files_are_preserved():
    baseline=json.loads((ROOT/'docs/science_before_mvp.json').read_text())
    for path,expected in baseline.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path


def test_zero_historical_demand_is_displayed_as_zero(monkeypatch,tmp_path):
    import streamlit as st
    st.cache_data.clear()
    with TestClient(create_app(db_path=tmp_path/'zero.sqlite')) as client:
        def route(method,url,**kwargs):
            kwargs.pop('timeout',None)
            return client.request(method,url.replace('http://127.0.0.1:8000',''),**kwargs)
        monkeypatch.setenv('PRICING_API_URL','http://127.0.0.1:8000')
        monkeypatch.setattr(httpx,'request',route)
        at=AppTest.from_file(str(ROOT/'pricing/ui.py'),default_timeout=20).run()
        next(r for r in at.radio if r.label=='Origem da demanda-base').set_value('MovingAverage4 histórico').run()
        pid=next(s for s in at.selectbox if s.label=='Produto').value
        zero_week=next(row['week'] for row in client.app.state.catalog.history[pid] if row['base_demand']==0)
        next(s for s in at.selectbox if s.label=='Semana histórica de referência').set_value(zero_week).run()
        demand=next(n for n in at.number_input if n.label=='Demanda-base (unidades/semana)')
        assert demand.value==0 and demand.disabled
        next(b for b in at.button if b.label=='Comparar preços').click().run()
        assert not at.exception
        assert at.session_state['result']['base_demand']==0
        assert at.session_state['result']['recommended_estimated_revenue']==0
    st.cache_data.clear()


def test_ui_handles_non_json_error_and_recovers(monkeypatch,tmp_path):
    import streamlit as st
    st.cache_data.clear()
    with TestClient(create_app(db_path=tmp_path/'recovery.sqlite')) as client:
        broken=[True]
        def route(method,url,**kwargs):
            if broken[0]:
                return httpx.Response(503,text='<html>Service unavailable</html>')
            kwargs.pop('timeout',None)
            return client.request(method,url.replace('http://127.0.0.1:8000',''),**kwargs)
        monkeypatch.setenv('PRICING_API_URL','http://127.0.0.1:8000')
        monkeypatch.setattr(httpx,'request',route)
        at=AppTest.from_file(str(ROOT/'pricing/ui.py'),default_timeout=20).run()
        assert not at.exception and len(at.error)==1
        broken[0]=False
        next(b for b in at.button if b.label=='Tentar novamente').click().run()
        assert not at.exception and not at.error
        next(b for b in at.button if b.label=='Comparar preços').click().run()
        assert not at.exception and len(at.metric)==7
    st.cache_data.clear()
