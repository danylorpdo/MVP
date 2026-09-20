"""Painéis point-in-time e benchmark temporal de vendas entregues por semana de compra."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1]/'artifacts/mplconfig'))
import hashlib, json, platform
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT=Path(__file__).resolve().parents[1]
TRAIN_END=pd.Timestamp('2018-01-01')
SELECT_AT=pd.Timestamp('2018-05-01')
WEEKS=pd.date_range('2017-01-02','2018-08-20',freq='7D')
NUM=['units_lag_1','units_lag_2','units_lag_4','units_mean_4w','units_std_4w','active_weeks_8w','weeks_since_last_sale','last_observed_price','price_age_weeks','price_missing','price_change_last_observed','freight_median_lag','sellers_count_4w','category_units_lag_1','category_units_mean_4w','week_sin','week_cos','time_index','history_weeks']
CAT=['category']
FEATURES=NUM+CAT
CONFIG={'seed':42,'target':'Itens de pedidos entregues, agrupados pela semana da compra; alvo retrospectivo, não demanda latente','train_end_exclusive':str(TRAIN_END),'selection_at':str(SELECT_AT),'week_policy':'segunda a domingo; excluir semana de 2018-04-30 que cruza validação/teste','eligibility':{'min_orders':20,'min_active_weeks':8,'min_prices':2,'available_before':str(TRAIN_END)},'label_policy':'Treino usa contagem confirmada antes de 2018-01-01; seleção usa contagem confirmada antes de 2018-05-01. Alvo eventual preservado separadamente para avaliação retrospectiva. Rótulos disponíveis são censurados à direita.','selection':'menor MAE na validação com rótulo disponível em 2018-05-01; desempate RMSE e nome; inclui baselines','refit':False,'negative_predictions':'clip em zero, comum a todos','numeric_features':NUM,'categorical_features':CAT}

def load_raw():
    r=ROOT/'data/raw'
    o=pd.read_csv(r/'olist_orders_dataset.csv')
    i=pd.read_csv(r/'olist_order_items_dataset.csv')
    p=pd.read_csv(r/'olist_products_dataset.csv')
    assert o.order_id.is_unique and p.product_id.is_unique
    assert not i.duplicated(['order_id','order_item_id']).any()
    x=i.merge(o,on='order_id',validate='many_to_one').merge(p[['product_id','product_category_name']],on='product_id',validate='many_to_one')
    x['purchase']=pd.to_datetime(x.order_purchase_timestamp)
    x['available']=pd.to_datetime(x.order_delivered_customer_date)
    x['week']=x.purchase.dt.to_period('W-SUN').dt.start_time
    x['category']=x.product_category_name.fillna('sem_categoria')
    x['price_cents']=(x.price*100).round().astype(int)
    return x

def known_deliveries(x,cutoff):
    return x[x.order_status.eq('delivered') & x.available.lt(cutoff) & x.purchase.lt(cutoff)]

def select_entities(x):
    tr=known_deliveries(x,TRAIN_END)
    tr=tr[tr.week.isin(WEEKS[WEEKS<TRAIN_END])]
    g=tr.groupby('product_id').agg(orders=('order_id','nunique'),weeks=('week','nunique'),prices=('price_cents','nunique'))
    ids=g[(g.orders>=20)&(g.weeks>=8)&(g.prices>=2)].index.tolist()
    # Somente categorias vistas nas transações disponíveis de treino.
    cw=tr.groupby(['category','week']).size().unstack(fill_value=0).reindex(columns=WEEKS[WEEKS<TRAIN_END],fill_value=0)
    eligible=(cw.gt(0).mean(axis=1)>=.9)&(cw.median(axis=1)>=20)&cw.index.to_series().ne('sem_categoria')
    cats=cw.index[eligible].tolist()
    # Categoria de cada produto obtida apenas a partir dos registros de treino.
    mapping=tr.drop_duplicates('product_id').set_index('product_id').category.to_dict()
    return sorted(ids),sorted(cats),mapping

def split_for(w):
    if w+pd.Timedelta(days=7)<=TRAIN_END:return 'train'
    if w>=TRAIN_END and w+pd.Timedelta(days=7)<=SELECT_AT:return 'validation'
    if w>=SELECT_AT:return 'test'
    return 'boundary_excluded'

def make_panel(x,entities,mapping,level):
    key='product_id' if level=='product' else 'category'
    delivered=x[x.order_status.eq('delivered')].copy()
    targets=delivered.groupby([key,'week']).size()
    trlabels=known_deliveries(x,TRAIN_END).groupby([key,'week']).size()
    vallabels=known_deliveries(x,SELECT_AT).groupby([key,'week']).size()
    rows=[]
    for w in WEEKS:
        known=known_deliveries(x,w)
        # Unicamente datas de compra anteriores e entregas confirmadas antes de w.
        known=known[known.week.ge(WEEKS[0])]
        assert known.empty or (known.available.max()<w and known.purchase.max()<w)
        groups={k:g for k,g in known.groupby(key)}
        cat_counts=known.groupby(['category','week']).size()
        for entity in entities:
            category=mapping[entity] if level=='product' else entity
            h=groups.get(entity,known.iloc[:0])
            counts=h.groupby('week').size()
            prev=[w-pd.Timedelta(weeks=j) for j in range(1,9)]
            vals=[float(counts.get(v,0)) for v in prev]
            hist_weeks=int((w-WEEKS[0]).days//7)
            prices=h.groupby('week').price.median().sort_index()
            recent=h[h.week.ge(w-pd.Timedelta(weeks=4))]
            catvals=[float(cat_counts.get((category,v),0)) for v in prev[:4]]
            last_price=prices.iloc[-1] if len(prices) else np.nan
            row={'entity_id':entity,'category':category,'week':w,'split':split_for(w),
                 'units_lag_1':vals[0],'units_lag_2':vals[1] if hist_weeks>=2 else np.nan,'units_lag_4':vals[3] if hist_weeks>=4 else np.nan,
                 'units_mean_4w':np.mean(vals[:4]) if hist_weeks>=4 else np.nan,'units_std_4w':np.std(vals[:4]) if hist_weeks>=4 else np.nan,
                 'active_weeks_8w':sum(v>0 for v in vals[:min(hist_weeks,8)]),
                 'weeks_since_last_sale':(w-counts.index.max()).days/7 if len(counts) else np.nan,
                 'last_observed_price':last_price,'price_age_weeks':(w-prices.index[-1]).days/7 if len(prices) else np.nan,
                 'price_missing':int(not len(prices)),
                 'price_change_last_observed':prices.iloc[-1]/prices.iloc[-2]-1 if len(prices)>=2 else np.nan,
                 'freight_median_lag':recent.freight_value.median(), 'sellers_count_4w':recent.seller_id.nunique(),
                 'category_units_lag_1':catvals[0],'category_units_mean_4w':np.mean(catvals) if hist_weeks>=4 else np.nan,
                 'week_sin':np.sin(2*np.pi*w.isocalendar().week/52.18),'week_cos':np.cos(2*np.pi*w.isocalendar().week/52.18),
                 'time_index':hist_weeks,'history_weeks':hist_weeks,
                 'target_units':int(targets.get((entity,w),0)),
                 'label_available_train':int(trlabels.get((entity,w),0)),
                 'label_available_selection':int(vallabels.get((entity,w),0)),
                 'max_source_available':h.available.max(),'max_source_purchase':h.purchase.max()}
            row['no_recorded_sale']=row['target_units']==0 # metadado de avaliação, nunca feature
            row['availability_state']='unknown' # zero não significa oferta ativa ou demanda zero
            rows.append(row)
    return pd.DataFrame(rows).sort_values(['week','entity_id']).reset_index(drop=True)

def metric(y,p):
    return {'MAE':float(mean_absolute_error(y,p)),'RMSE':float(np.sqrt(mean_squared_error(y,p))),'R2':float(r2_score(y,p)) if len(y)>1 and np.var(y)>0 else None}

def model_pipeline(name):
    numeric=[('impute',SimpleImputer(strategy='median',keep_empty_features=True))]
    if name in ['Linear','Polynomial']:
        numeric += [('scale',StandardScaler())]
    if name=='Polynomial':numeric += [('poly',PolynomialFeatures(degree=2,include_bias=False)),('scale_poly',StandardScaler())]
    pre=ColumnTransformer([('num',Pipeline(numeric),NUM),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])
    model={'Linear':LinearRegression(),'Polynomial':LinearRegression(),'RandomForest':RandomForestRegressor(n_estimators=200,max_depth=8,min_samples_leaf=5,max_features=1.0,random_state=42,n_jobs=2),'GradientBoosting':GradientBoostingRegressor(n_estimators=150,learning_rate=.05,max_depth=2,min_samples_leaf=10,loss='squared_error',random_state=42)}[name]
    return Pipeline([('preprocess',pre),('regressor',model)])

def evaluate(panel,level):
    art=ROOT/'artifacts'/level;art.mkdir(parents=True,exist_ok=True)
    # 4 semanas iniciais são aquecimento para todos os métodos.
    usable=panel[(panel.history_weeks>=4)&panel.split.ne('boundary_excluded')].copy()
    train=usable[usable.split.eq('train')]
    X=train[FEATURES]; y=train.label_available_train
    all_predictions=[]; metrics=[]; fitted={}; params={}
    for name in ['PreviousWeek','MovingAverage4','Linear','Polynomial','RandomForest','GradientBoosting']:
        print(level,name,flush=True)
        estimator=None
        if name not in ['PreviousWeek','MovingAverage4']:
            estimator=model_pipeline(name);estimator.fit(X,y);fitted[name]=estimator
            params[name]=estimator.get_params(deep=True)
        for split in ['train','validation','test']:
            part=usable[usable.split.eq(split)].copy()
            if name=='PreviousWeek':raw=part.units_lag_1.to_numpy()
            elif name=='MovingAverage4':raw=part.units_mean_4w.to_numpy()
            else:raw=estimator.predict(part[FEATURES])
            pred=np.maximum(raw,0)
            # Alvo eventual somente para avaliação; nunca usado para fit/seleção.
            for label,col in [('eventual','target_units')]+([('available','label_available_train')] if split=='train' else [('available','label_available_selection')] if split=='validation' else []):
                metrics.append({'level':level,'model':name,'split':split,'label':label,'n':len(part),'negative_raw_predictions':int((raw<0).sum()),**metric(part[col],pred)})
            pr=part[['entity_id','category','week','split','target_units','label_available_train','label_available_selection','no_recorded_sale']].copy()
            pr['model']=name;pr['prediction']=pred;pr['error']=pred-pr.target_units
            all_predictions.append(pr)
    met=pd.DataFrame(metrics)
    ranking=met[(met.split=='validation')&(met.label=='available')].sort_values(['MAE','RMSE','model'])
    winner=ranking.iloc[0]['model']
    best_ml=ranking[~ranking.model.isin(['PreviousWeek','MovingAverage4'])].iloc[0]['model']
    # Artefato campeão inclui baseline se superar ML; artefato ML guardado separadamente.
    bundle={'name':winner,'estimator':fitted.get(winner),'baseline_feature':{'PreviousWeek':'units_lag_1','MovingAverage4':'units_mean_4w'}.get(winner),'features':FEATURES,'prediction_postprocess':'maximum(prediction,0)','config':CONFIG,'level':level}
    joblib.dump(bundle,art/'chosen_model.joblib')
    joblib.dump({**bundle,'name':best_ml,'estimator':fitted[best_ml],'baseline_feature':None},art/'best_ml_model.joblib')
    (art/'parameters.json').write_text(json.dumps(params,indent=2,default=str))
    predictions=pd.concat(all_predictions,ignore_index=True)
    predictions.to_csv(art/'predictions.csv',index=False)
    met.to_csv(art/'metrics.csv',index=False)
    for grouping in ['entity_id','category']:
        errors=[]
        for (name,split,group),v in predictions[predictions.split.ne('train')].groupby(['model','split',grouping]):
            errors.append({'model':name,'split':split,grouping:group,'n':len(v),'actual_units':int(v.target_units.sum()),'mean_error':float(v.error.mean()),**metric(v.target_units,v.prediction)})
        pd.DataFrame(errors).to_csv(ROOT/'reports'/f'{level}_errors_by_{grouping}.csv',index=False)
    # Erro em semanas com e sem transação evita que zeros escondam desempenho ruim.
    segments=[]
    for (name,split,zero),v in predictions.groupby(['model','split','no_recorded_sale']):
        segments.append({'model':name,'split':split,'no_recorded_sale':bool(zero),'n':len(v),**metric(v.target_units,v.prediction)})
    pd.DataFrame(segments).to_csv(ROOT/'reports'/f'{level}_errors_by_activity.csv',index=False)
    t=met[(met.label=='eventual')&met.split.isin(['validation','test'])].pivot(index='model',columns='split',values='MAE')
    ax=t.plot.bar(figsize=(10,5),color=['#4388b8','#e99c42']);ax.set_ylabel('MAE — unidades por semana');ax.set_title(f'{level}: comparação temporal (alvo eventual)');ax.tick_params(axis='x',rotation=25);plt.tight_layout();plt.savefig(ROOT/'reports/figures'/f'{level}_mae.png',dpi=150);plt.close()
    selected=predictions[(predictions.model==winner)&predictions.split.ne('train')]
    weekly=selected.groupby('week')[['target_units','prediction']].sum()
    ax=weekly.plot(figsize=(10,4));ax.set_title(f'{level}: totais semanais — {winner}');ax.set_ylabel('Unidades');plt.tight_layout();plt.savefig(ROOT/'reports/figures'/f'{level}_weekly.png',dpi=150);plt.close()
    # Verifica se o artefato serializado reproduz as previsões.
    loaded=joblib.load(art/'chosen_model.joblib'); sample=usable[usable.split=='test']
    pp=loaded['estimator'].predict(sample[FEATURES]) if loaded['estimator'] is not None else sample[loaded['baseline_feature']].to_numpy()
    expected=predictions[(predictions.model==winner)&(predictions.split=='test')].prediction
    np.testing.assert_allclose(np.maximum(pp,0),expected)
    info={'winner':winner,'best_ml':best_ml,'entities':int(panel.entity_id.nunique()),'rows_panel':len(panel),'rows_used':len(usable),'splits':{},'selection_ranking':ranking[['model','MAE','RMSE']].to_dict('records')}
    for split,v in usable.groupby('split'):
        info['splits'][split]={'rows':len(v),'weeks':int(v.week.nunique()),'start':str(v.week.min().date()),'end_week_start':str(v.week.max().date()),'target_units':int(v.target_units.sum()),'zero_fraction':float(v.no_recorded_sale.mean()),'available_label_units':int(v.label_available_train.sum()) if split=='train' else int(v.label_available_selection.sum()) if split=='validation' else None}
    (art/'summary.json').write_text(json.dumps(info,indent=2))
    return info,met

def run():
    for p in ['artifacts','reports/figures','data/processed']:(ROOT/p).mkdir(parents=True,exist_ok=True)
    x=load_raw();ids,cats,mapping=select_entities(x)
    (ROOT/'artifacts/config.json').write_text(json.dumps(CONFIG,indent=2,ensure_ascii=False))
    (ROOT/'artifacts/selection.json').write_text(json.dumps({'products':ids,'categories':cats,'product_categories':{k:mapping[k] for k in ids}},indent=2))
    allmetrics=[]; summaries={}
    for level,entities in [('product',ids),('category',cats)]:
        print('Building',level,len(entities),flush=True)
        panel=make_panel(x,entities,mapping,level)
        panel.to_csv(ROOT/'data/processed'/f'{level}_week_features.csv',index=False)
        # Auditoria ponto no tempo para todas as linhas.
        for c in ['max_source_available','max_source_purchase']:
            assert (panel[c].isna()|panel[c].lt(panel.week)).all()
        info,met=evaluate(panel,level);summaries[level]=info;allmetrics.append(met)
    pd.concat(allmetrics).to_csv(ROOT/'reports/model_metrics.csv',index=False)
    (ROOT/'artifacts/run_summary.json').write_text(json.dumps(summaries,indent=2))
    import sklearn
    manifest={'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'sklearn':sklearn.__version__,'raw_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data/raw').glob('*.csv'))},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT/'artifacts/run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(summaries,indent=2),flush=True)
if __name__=='__main__':run()
