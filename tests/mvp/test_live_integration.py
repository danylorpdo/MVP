"""Integração real HTTP em portas livres; banco temporário, sem alterar o histórico da demo."""
import os
import socket
import subprocess
import sys
import time

import httpx
import streamlit as st
from streamlit.testing.v1 import AppTest
from pricing.artifacts import ROOT


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_ready(process,url):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if process.poll() is not None:
            raise AssertionError(f'Servidor encerrou com código {process.returncode}')
        try:
            if httpx.get(url,timeout=1).status_code==200:
                return
        except httpx.RequestError:
            pass
        time.sleep(.1)
    raise AssertionError(f'Servidor não ficou pronto: {url}')


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def test_real_http_ui_api_engine_and_restart(monkeypatch,tmp_path):
    api_port,ui_port=free_port(),free_port()
    api_url=f'http://127.0.0.1:{api_port}'
    env=os.environ|{'PRICING_DB_PATH':str(tmp_path/'live.sqlite'),'PRICING_API_URL':api_url}
    api_cmd=[sys.executable,'-m','uvicorn','pricing.api:app','--host','127.0.0.1','--port',str(api_port)]
    ui_cmd=[sys.executable,'-m','streamlit','run','pricing/ui.py','--server.address=127.0.0.1',f'--server.port={ui_port}','--server.headless=true']
    monkeypatch.setenv('PRICING_API_URL',api_url)
    processes=[]
    st.cache_data.clear()
    try:
        with (tmp_path/'servers.log').open('w') as log:
            for cmd,url in [(api_cmd,api_url+'/health'),(ui_cmd,f'http://127.0.0.1:{ui_port}/_stcore/health')]:
                proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                processes.append(proc)
                wait_ready(proc,url)
            assert httpx.get(f'http://127.0.0.1:{ui_port}',timeout=5).status_code==200
            assert httpx.get(api_url+'/docs',timeout=5).status_code==200
            assert '/api/v1/simulations' in httpx.get(api_url+'/openapi.json',timeout=5).json()['paths']
            at=AppTest.from_file(str(ROOT/'pricing/ui.py'),default_timeout=20).run()
            assert not at.exception and not at.error
            next(b for b in at.button if b.label=='Comparar preços').click().run()
            assert not at.exception and len(at.metric)==7 and len(at.dataframe)==1
            assert len(at.get('arrow_vega_lite_chart'))==2
            manual=at.session_state['result']
            assert httpx.get(api_url+'/api/v1/simulations/'+manual['id']).json()['result']==manual
            next(r for r in at.radio if r.label=='Origem da demanda-base').set_value('MovingAverage4 histórico').run()
            next(b for b in at.button if b.label=='Comparar preços').click().run()
            assert not at.exception and at.session_state['result']['demand_source']=='moving_average4'
            next(r for r in at.radio if r.label=='Navegação').set_value('Histórico').run()
            assert not at.exception and len(at.metric)==7
            next(r for r in at.radio if r.label=='Navegação').set_value('Metodologia').run()
            assert not at.exception and len(at.metric)==1
            stop(processes.pop(0))
            proc=subprocess.Popen(api_cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            processes.append(proc)
            wait_ready(proc,api_url+'/health')
            assert len(httpx.get(api_url+'/api/v1/simulations').json())==2
            assert httpx.get(api_url+'/api/v1/simulations/'+manual['id']).json()['result']==manual
    finally:
        for proc in processes:
            stop(proc)
        st.cache_data.clear()
