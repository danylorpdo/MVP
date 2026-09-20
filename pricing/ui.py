import json
import os
import httpx
import pandas as pd
import altair as alt
import streamlit as st

API = os.getenv('PRICING_API_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='Pricing Lab | Marketplace', page_icon='📊', layout='wide')


def call(method, path, **kwargs):
    try:
        response = httpx.request(method, API+path, timeout=15, **kwargs)
        if response.is_error:
            try:
                body = response.json()
                detail = body.get('detail', response.text) if isinstance(body, dict) else response.text
            except ValueError:
                detail = response.text or 'Resposta de erro sem detalhes.'
            raise RuntimeError(f'API {response.status_code}: {detail}')
        try:
            return response.json()
        except ValueError:
            raise RuntimeError('A API retornou uma resposta inválida. Verifique o serviço configurado.')
    except httpx.RequestError:
        raise RuntimeError('Não foi possível conectar à API. Verifique se ela está iniciada na porta 8000.')


def brl(value):
    return 'R$ '+f'{value:,.2f}'.replace(',','X').replace('.',',').replace('X','.')


@st.cache_data(ttl=60)
def catalog():
    return call('GET','/api/v1/products'), call('GET','/api/v1/metadata')


def display_result(result):
    st.divider()
    st.subheader('Resultado do cenário')
    st.caption('Última simulação salva. Alterações no formulário só se aplicam ao clicar em Comparar preços.')
    st.caption(f"{result['category'].replace('_',' ')} · Produto {result['product_id']} · Horizonte: {result['horizon']}")
    a,b,c = st.columns(3)
    a.metric('Preço recomendado na simulação',brl(result['recommended_price']),f"{result['change_pct']:+.2f}% sobre {brl(result['current_price'])}")
    b.metric('Receita estimada — preço recomendado',brl(result['recommended_estimated_revenue']))
    c.metric('Receita estimada — preço atual',brl(result['current_estimated_revenue']))
    a,b,c,d=st.columns(4)
    a.metric('Demanda-base / semana',f"{result['base_demand']:.2f}")
    b.metric('Demanda ajustada / semana',f"{result['adjusted_demand']:.2f}")
    c.metric('Unidades vendáveis',f"{result['sellable_units']:.2f}")
    d.metric('Estoque informado',str(result['stock']))
    st.warning('\n\n'.join('• '+v for v in result['warnings']))
    frame=pd.DataFrame(result['scenarios'])
    st.subheader('Preço, demanda e receita')
    left,right=st.columns(2)
    demand=frame[['price','adjusted_demand','sellable_units']].melt('price',var_name='Série',value_name='Unidades')
    demand['Série']=demand['Série'].map({'adjusted_demand':'Demanda ajustada','sellable_units':'Limitada pelo estoque'})
    chart=alt.Chart(demand).mark_line(point=True).encode(x=alt.X('price:Q',title='Preço candidato (R$)',scale=alt.Scale(zero=False)),y=alt.Y('Unidades:Q',title='Unidades por semana'),color='Série:N',tooltip=['price:Q','Série:N','Unidades:Q']).properties(height=270)
    left.altair_chart(chart,use_container_width=True)
    revenue=alt.Chart(frame).mark_line(point=True,color='#0d9488').encode(x=alt.X('price:Q',title='Preço candidato (R$)',scale=alt.Scale(zero=False)),y=alt.Y('estimated_revenue:Q',title='Receita semanal estimada (R$)'),tooltip=['price:Q','estimated_revenue:Q']).properties(height=270)
    best=alt.Chart(pd.DataFrame([{'price':result['recommended_price']}])).mark_rule(color='#d97706',strokeDash=[4,4]).encode(x='price:Q')
    right.altair_chart(revenue+best,use_container_width=True)
    st.caption('Linha tracejada: candidato com maior receita estimada na grade. Unidades fracionárias representam expectativas, não vendas realizadas.')
    st.subheader('Todos os cenários avaliados')
    table=frame.copy()
    table['warnings']=table.warnings.apply(lambda x:'; '.join(x) if x else 'Sem alerta adicional')
    table['outside_historical_range']=table.outside_historical_range.map({True:'Fora da faixa',False:'Dentro da faixa'})
    table=table.rename(columns={'price':'Preço (R$)','change_pct':'Variação (%)','response_factor':'Fator de resposta','adjusted_demand':'Demanda ajustada','sellable_units':'Unidades vendáveis','estimated_revenue':'Receita estimada (R$)','outside_historical_range':'Faixa histórica','warnings':'Avisos'})
    st.dataframe(table,hide_index=True,width="stretch")
    st.download_button('Baixar resultado em JSON',json.dumps(result,indent=2,ensure_ascii=False),file_name=f"simulacao-{result['id']}.json",mime='application/json')
    with st.expander('Rastreabilidade e versões'):
        st.write('Simulação:',result['id'])
        st.write('Criada em UTC:',result['created_at'])
        st.write('Semana histórica de referência:',result['demand_reference_week'] or 'Não se aplica — demanda manual')
        st.write('Elasticidade compartilhada:',result['elasticity'])
        st.json(result['artifact_versions'])


st.sidebar.title('Pricing Lab')
st.sidebar.caption('Danylo & William · Tema 7')
page=st.sidebar.radio('Navegação',['Simular','Histórico','Metodologia'])
st.sidebar.info('Protótipo acadêmico. Associações históricas não comprovam efeitos de alterar preços.')
st.title('Precificação dinâmica para marketplace')
st.caption('Compare cenários semanais de preço com demanda-base, estoque informado e resposta experimental ao preço.')
try:
    products, meta=catalog()
except RuntimeError as exc:
    st.error(str(exc))
    if st.button('Tentar novamente'):
        st.cache_data.clear();st.rerun()
    st.stop()

if page=='Simular':
    lookup={p['product_id']:p for p in products}
    # Exemplo com histórico positivo e suporte individual primeiro, sem alterar o catálogo científico.
    ordered=sorted(products,key=lambda p:(not p['sufficient_individual_support'],-((p['latest_snapshot'] or {}).get('base_demand',0)),p['product_id']))
    pid=st.selectbox('Produto',options=[p['product_id'] for p in ordered],format_func=lambda pid:lookup[pid]['category'].replace('_',' ')+' · '+pid[:12])
    product=lookup[pid]
    st.caption((f"ID completo: {pid} · Faixa de preço observada no treino: {brl(product['min_price'])} a {brl(product['max_price'])}").replace('$', r'\$'))
    mode=st.radio('Origem da demanda-base',['Informar demanda semanal','MovingAverage4 histórico'],horizontal=True)
    historical=mode=='MovingAverage4 histórico'
    week=None
    if historical:
        try:
            history=call('GET',f'/api/v1/products/{pid}/history')
        except RuntimeError as exc:
            st.error(str(exc));st.stop()
        if not history:
            st.warning('Este produto não tem histórico disponível. Use a demanda manual.')
            st.stop()
        week=st.selectbox('Semana histórica de referência',[row['week'] for row in history],index=len(history)-1)
        snapshot=next(row for row in history if row['week']==week)
        st.info(f"Demanda histórica disponível: {snapshot['base_demand']:.2f} unidades/semana. Referência {week}; não é uma previsão para hoje.")
    else:
        snapshot=product['latest_snapshot']
    default_price=(snapshot or {}).get('last_observed_price') or product['min_price']
    with st.form('simulation_form'):
        c1,c2,c3=st.columns(3)
        price=c1.number_input('Preço atual (R$)',min_value=.01,max_value=1_000_000_000.,value=round(float(default_price),2),step=1.,format='%.2f',key='price_'+pid+'_'+str(week))
        stock=c2.number_input('Estoque disponível (unidades)',min_value=0,max_value=1_000_000_000,value=20,step=1)
        demand=c3.number_input('Demanda-base (unidades/semana)',min_value=0.,max_value=1_000_000_000.,value=float(snapshot['base_demand'] if snapshot is not None else 10),step=1.,disabled=historical,key='demand_'+pid+'_'+str(week))
        c1,c2,c3=st.columns(3)
        down=c1.number_input('Redução máxima (%)',min_value=0.,max_value=10.,value=10.,step=1.)
        up=c2.number_input('Aumento máximo (%)',min_value=0.,max_value=10.,value=10.,step=1.)
        step=c3.number_input('Passo da grade (%)',min_value=.1,max_value=10.,value=5.,step=.5)
        submitted=st.form_submit_button('Comparar preços',type='primary')
    if submitted:
        payload={'product_id':pid,'current_price':round(price,2),'stock':int(stock),'demand_source':'moving_average4' if historical else 'manual','max_decrease_pct':down,'max_increase_pct':up,'step_pct':step}
        if historical:payload['reference_week']=week
        else:payload['base_demand']=demand
        try:
            st.session_state['result']=call('POST','/api/v1/simulations',json=payload)
            st.success('Cenários calculados e salvos no histórico local.')
        except RuntimeError as exc:
            st.session_state.pop('result',None);st.error(str(exc))
    if st.session_state.get('result'):
        display_result(st.session_state['result'])

elif page=='Histórico':
    st.subheader('Simulações salvas')
    try:
        rows=call('GET','/api/v1/simulations?limit=50')
        if not rows:st.info('Nenhuma simulação salva. Faça a primeira na tela Simular.')
        else:
            st.dataframe(pd.DataFrame(rows).rename(columns={'created_at':'Criada em UTC','product_id':'Produto','current_price':'Preço atual','recommended_price':'Preço recomendado','recommended_estimated_revenue':'Receita estimada'}),hide_index=True,width="stretch")
            sid=st.selectbox('Abrir simulação',[r['id'] for r in rows])
            saved=call('GET',f'/api/v1/simulations/{sid}')
            display_result(saved['result'])
    except RuntimeError as exc:st.error(str(exc))

else:
    st.subheader('Dois experimentos, duas responsabilidades')
    st.markdown('**Demanda-base:** MovingAverage4 permanece o campeão do experimento de previsão. Também é possível informar uma expectativa semanal manual.\n\n**Resposta ao preço:** elasticidade log-log compartilhada, estimada em semanas com transações. Sua aplicação à demanda-base é uma hipótese experimental.')
    st.metric('Elasticidade compartilhada observacional',f"{meta['elasticity']:.4f}")
    st.code('fator = (preço candidato / preço atual) ** elasticidade\ndemanda ajustada = demanda-base × fator\nunidades vendáveis = min(demanda ajustada, estoque)\nreceita estimada = preço candidato × unidades vendáveis',language=None)
    st.markdown('A grade inclui o preço atual e candidatos dentro dos limites escolhidos, no máximo ±10%. Os preços têm duas casas decimais. No empate de receita estimada, preferimos a menor alteração de preço.')
    st.warning('Dados observacionais da Olist, sem estoque nem preço ofertado continuamente. O preço realizado é um proxy. Não há demonstração de causalidade, lucro ou ganho real. Faixas históricas e suporte insuficiente são avisados na simulação; extrapolações não são ocultadas.')
    with st.expander('Versões dos artefatos congelados'):
        st.json(meta['artifact_versions'])
