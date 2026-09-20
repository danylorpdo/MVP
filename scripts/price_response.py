"""Experimento independente, observacional e condicional às semanas ativas."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'artifacts/price_response/mplconfig')
import hashlib,json,platform
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler,OneHotEncoder,PolynomialFeatures
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score

A=ROOT/'artifacts/price_response';R=ROOT/'reports/price_response';D=ROOT/'data/processed/price_response'
HIST=['units_lag_1','units_lag_2','units_lag_4','units_mean_4w','units_std_4w','active_weeks_8w','weeks_since_last_sale','price_age_weeks','category_units_lag_1','category_units_mean_4w','week_sin','week_cos','time_index']
NUM=HIST+['log_last_observed_price','log_price_ratio']
CAT=['entity_id','category']
FEATURES=NUM+CAT
GRID=[.90,.95,1.,1.05,1.10]
CONFIG={'seed':42,'price_proxy':'Mediana do preço realizado nos itens da semana de compra; somente cenário, não oferta contínua','target':'Itens de pedidos entregues por produto e semana da compra, condicionado a transação/preço observado','frozen_selection':'artifacts/selection.json','selection_metric':'MAE na validação com vendas e preço confirmados antes de 2018-05-01','train_labels':'Entregas confirmadas antes de 2018-01-01; somente label_available_train>0','eval_labels':'target_units eventual, somente semanas ativas','scenario_fields':['scenario_price','price_ratio_to_last_observed','price_change_pct','log_price_ratio'],'input_features':FEATURES,'sensitivity_grid':GRID,'flags':{'flat_relative_range':.01,'large_relative_range':1.0,'large_factor_vs_current':2.,'near_zero_base_prediction':.1},'polynomial':'grau 2 sobre numéricas; Ridge alpha=1 fixado antes da execução, sem tuning','scope':'modelos compartilhados com produto e categoria codificados no treino','no_monotonicity':True,'no_refit':True}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def protected_files():
    files=[]
    for folder in ['artifacts','reports','data/processed','scripts']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and 'price_response' not in str(p.relative_to(ROOT)) and '__pycache__' not in str(p):files.append(p)
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}
def scenario(df,price):
    v=df.copy();v['scenario_price']=np.asarray(price)
    v['price_ratio_to_last_observed']=v.scenario_price/v.last_observed_price
    v['price_change_pct']=100*(v.price_ratio_to_last_observed-1)
    v['log_price_ratio']=np.log(v.price_ratio_to_last_observed)
    v['log_last_observed_price']=np.log(v.last_observed_price)
    return v

def data():
    selection=json.loads((ROOT/'artifacts/selection.json').read_text())
    p=pd.read_csv(ROOT/'data/processed/product_week_features.csv',parse_dates=['week','max_source_available','max_source_purchase'])
    assert set(p.entity_id)==set(selection['products'])
    for col in ['max_source_available','max_source_purchase']:
        assert (p[col].isna()|p[col].lt(p.week)).all()
    o=pd.read_csv(ROOT/'data/raw/olist_orders_dataset.csv')
    i=pd.read_csv(ROOT/'data/raw/olist_order_items_dataset.csv')
    x=i.merge(o,on='order_id',validate='many_to_one')
    x=x[x.product_id.isin(selection['products'])&x.order_status.eq('delivered')].copy()
    x['week']=pd.to_datetime(x.order_purchase_timestamp).dt.to_period('W-SUN').dt.start_time
    x['available']=pd.to_datetime(x.order_delivered_customer_date)
    for name,cutoff in [('price_eventual',None),('price_train','2018-01-01'),('price_selection','2018-05-01')]:
        source=x if cutoff is None else x[x.available.lt(cutoff)]
        med=source.groupby(['product_id','week']).price.median().rename(name).reset_index().rename(columns={'product_id':'entity_id'})
        p=p.merge(med,on=['entity_id','week'],how='left',validate='one_to_one')
    p=p[(p.history_weeks>=4)&p.split.ne('boundary_excluded')].copy()
    # Exige referência passada genuína para razões; não inventa preço-base.
    mask=p.target_units.gt(0)&p.price_eventual.gt(0)&p.last_observed_price.gt(0)
    count={'panel_eligible_rows':len(p),'active_rows':int(p.target_units.gt(0).sum()),'active_missing_last_price':int((p.target_units.gt(0)&~p.last_observed_price.gt(0)).sum())}
    full=scenario(p[mask],p.loc[mask,'price_eventual'])
    train=full[full.split.eq('train')&full.label_available_train.gt(0)&full.price_train.gt(0)].copy()
    train=scenario(train,train.price_train);train['fit_units']=train.label_available_train
    available=full[full.split.eq('validation')&full.label_available_selection.gt(0)&full.price_selection.gt(0)].copy()
    available=scenario(available,available.price_selection);available['fit_units']=available.label_available_selection
    full.to_csv(D/'active_product_week.csv',index=False);train.to_csv(D/'train_asof.csv',index=False);available.to_csv(D/'validation_asof.csv',index=False)
    return full,train,available,count

def model(name,with_price=True):
    numeric=NUM if with_price else [c for c in NUM if c!='log_price_ratio']
    steps=[('impute',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]
    if name=='Polynomial':steps += [('poly',PolynomialFeatures(degree=2,include_bias=False)),('poly_scale',StandardScaler())]
    prep=ColumnTransformer([('numeric',Pipeline(steps),numeric),('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])
    reg={'Linear':LinearRegression(),'Polynomial':Ridge(alpha=1.),'RandomForest':RandomForestRegressor(n_estimators=200,max_depth=8,min_samples_leaf=5,random_state=42,n_jobs=2),'GradientBoosting':GradientBoostingRegressor(n_estimators=150,learning_rate=.05,max_depth=2,min_samples_leaf=10,random_state=42)}[name]
    return Pipeline([('preprocess',prep),('regressor',reg)])

def metrics(y,p):
    return {'MAE':float(mean_absolute_error(y,p)),'RMSE':float(np.sqrt(mean_squared_error(y,p))),'R2':float(r2_score(y,p)) if len(y)>1 and np.var(y)>0 else None}

# Log-log com intercepto por produto, calculado por transformação within.
# Slope não é causal; controles ausentes e seleção por venda permanecem.
def loglog_fit(train):
    t=train.copy();t['lp']=np.log(t.scenario_price);t['lq']=np.log(t.fit_units)
    g=t.groupby('entity_id')
    xp=t.lp-g.lp.transform('mean');yq=t.lq-g.lq.transform('mean')
    contrib=pd.DataFrame({'entity_id':t.entity_id,'xx':xp*xp,'xy':xp*yq}).groupby('entity_id')[['xx','xy']].sum()
    beta=float(contrib.xy.sum()/contrib.xx.sum())
    alpha=(t.lq-beta*t.lp).groupby(t.entity_id).mean().to_dict()
    fallback=float((t.lq-beta*t.lp).mean())
    rows=[];catbetas={}
    for category,v in t.groupby('category'):
        idx=v.index;den=float((xp.loc[idx]**2).sum())
        qualifies=len(v)>=40 and v.entity_id.nunique()>=3 and den>.01
        b=float((xp.loc[idx]*yq.loc[idx]).sum()/den) if qualifies else beta
        catbetas[category]=b
        rows.append({'category':category,'rows':len(v),'products':v.entity_id.nunique(),'within_log_price_ss':den,'own_slope':qualifies,'beta_used':b})
    cat_alpha=(t.lq-t.category.map(catbetas)*t.lp).groupby(t.entity_id).mean().to_dict()
    rng=np.random.default_rng(42);boot=[];arr=contrib.to_numpy()
    for _ in range(400):
        sample=arr[rng.integers(0,len(arr),size=len(arr))].sum(axis=0)
        if sample[0]>1e-10:boot.append(float(sample[1]/sample[0]))
    # Diagnóstico individual; apenas limiares de treino, não escolhido pelo sinal.
    per=[]
    for pid,v in t.groupby('entity_id'):
        xx=v.lp-v.lp.mean();yy=v.lq-v.lq.mean();den=float((xx**2).sum())
        eligible=len(v)>=12 and v.scenario_price.round(2).nunique()>=4 and v.scenario_price.std()/v.scenario_price.mean()>=.03 and v.scenario_price.max()/v.scenario_price.min()>=1.10
        b=float((xx*yy).sum()/den) if eligible and den>1e-8 else None
        per.append({'entity_id':pid,'category':v.category.iloc[0],'active_train_weeks':len(v),'weekly_prices':v.scenario_price.round(2).nunique(),'min_price':v.scenario_price.min(),'max_price':v.scenario_price.max(),'eligible_individual_slope':eligible,'beta':b})
    pd.DataFrame(per).to_csv(R/'individual_support.csv',index=False);pd.DataFrame(rows).to_csv(R/'category_elasticity.csv',index=False)
    b={'beta':beta,'intercepts':alpha,'fallback_intercept':fallback,'category_betas':catbetas,'category_intercepts':cat_alpha,'cluster_bootstrap_95pct':np.quantile(boot,[.025,.975]).tolist(),'bootstraps':len(boot),'interpretation':'elasticidade associativa within-produto nas semanas ativas; sem causalidade; retransf. exp sem correção de smearing (mediana geométrica)'}
    (A/'loglog.json').write_text(json.dumps(b,indent=2))
    return b

def predict(est,df,name):
    if name.startswith('LogLog'):
        beta=df.category.map(est['category_betas']).fillna(est['beta']) if name=='LogLogCategory' else est['beta']
        alphas=est['category_intercepts'] if name=='LogLogCategory' else est['intercepts']
        return np.exp(df.entity_id.map(alphas).fillna(est['fallback_intercept'])+beta*np.log(df.scenario_price))
    return est.predict(df[FEATURES])

def sensitivity(name,est,cases,train):
    bounds=train.groupby('entity_id').scenario_price.agg(['min','max'])
    trratio=train.price_ratio_to_last_observed
    allrows=[];curves=[]
    for scale in GRID:
        new=scenario(cases,cases.scenario_price*scale)
        # Todas as features não-preço invariantes.
        pd.testing.assert_frame_equal(cases[HIST+CAT+['log_last_observed_price']],new[HIST+CAT+['log_last_observed_price']])
        raw=predict(est,new,name);pred=np.maximum(raw,0)
        part=new[['entity_id','category','week','split','scenario_price','price_ratio_to_last_observed']].copy()
        part['case_id']=cases.index;part['model']=name;part['scale']=scale;part['raw_prediction']=raw;part['prediction']=pred
        low=part.entity_id.map(bounds['min']);high=part.entity_id.map(bounds['max'])
        part['outside_product_train_price']=(part.scenario_price<low)|(part.scenario_price>high)
        part['outside_train_ratio']=(part.price_ratio_to_last_observed<trratio.min())|(part.price_ratio_to_last_observed>trratio.max())
        allrows.append(part);curves.append(pred)
    mat=np.array(curves).T;rawtable=pd.concat(allrows,ignore_index=True)
    summaries=cases[['entity_id','category','week','split']].copy();summaries['model']=name;summaries['case_id']=cases.index
    summaries['q_minus10']=mat[:,0];summaries['q_current']=mat[:,2];summaries['q_plus10']=mat[:,-1]
    summaries['delta_units_plus10']=mat[:,-1]-mat[:,2]
    denom=np.where(mat[:,2]>.1,mat[:,2],np.nan)
    summaries['factor_plus10']=mat[:,-1]/denom
    summaries['relative_range']=(mat.max(axis=1)-mat.min(axis=1))/denom
    summaries['any_increase_with_price']=(np.diff(mat,axis=1)>1e-6).any(axis=1)
    summaries['increase_at_plus10']=mat[:,-1]>mat[:,2]+1e-6
    summaries['flat_response']=((mat.max(axis=1)-mat.min(axis=1))<=1e-6)|(summaries.relative_range<.01)
    summaries['near_zero_denominator']=mat[:,2]<=.1
    summaries['large_response']=summaries.relative_range>1.
    summaries['large_factor']=summaries.factor_plus10>2.
    rawmat=np.array([v.raw_prediction.to_numpy() for v in allrows]).T
    summaries['negative_raw_any']=(rawmat<0).any(axis=1)
    ext=np.array([v.outside_product_train_price.to_numpy() for v in allrows]).T
    summaries['any_outside_product_support']=ext.any(axis=1)
    return rawtable,summaries

def run():
    for folder in [A,R/'figures',D]:folder.mkdir(parents=True,exist_ok=True)
    before=protected_files();(A/'preserved_before.json').write_text(json.dumps(before,indent=2))
    (A/'config.json').write_text(json.dumps(CONFIG,indent=2,ensure_ascii=False))
    full,train,available,counts=data();loglog=loglog_fit(train)
    estimators={};params={};allmetrics=[];predictions=[];sens=[];curves=[]
    for name in ['Linear','Polynomial','RandomForest','GradientBoosting','LogLogPooled','LogLogCategory']:
        print('Fitting',name,flush=True)
        est=loglog if name.startswith('LogLog') else model(name)
        if not name.startswith('LogLog'):
            est.fit(train[FEATURES],train.fit_units);params[name]=est.get_params(deep=True)
        estimators[name]=est
        joblib.dump({'name':name,'estimator':est,'features':FEATURES,'config':CONFIG},A/f'{name}.joblib')
        evaluations=[('train_available',train,'fit_units'),('validation_available',available,'fit_units')]+[(split,full[full.split==split],'target_units') for split in ['validation','test']]
        for split,v,target in evaluations:
            raw=predict(est,v,name);pred=np.maximum(raw,0)
            allmetrics.append({'model':name,'split':split,'n':len(v),'negative_raw':int((raw<0).sum()),**metrics(v[target],pred)})
            pr=v[['entity_id','category','week']].copy();pr['model']=name;pr['split']=split;pr['actual']=v[target];pr['prediction']=pred;predictions.append(pr)
        raw,s=sensitivity(name,est,full[full.split.isin(['validation','test'])],train);curves.append(raw);sens.append(s)
    # Ablation pareada: mesma configuração, remove apenas o cenário de preço.
    # Teste diagnóstico predefinido, não altera a seleção.
    ablations=[]
    for name in ['Linear','Polynomial','RandomForest','GradientBoosting']:
        est=model(name,with_price=False);est.fit(train[FEATURES],train.fit_units)
        for split,v,target in [('validation_available',available,'fit_units'),('validation',full[full.split=='validation'],'target_units'),('test',full[full.split=='test'],'target_units')]:
            pred=np.maximum(est.predict(v[FEATURES]),0)
            ablations.append({'model':name,'split':split,**metrics(v[target],pred)})
    pd.DataFrame(ablations).to_csv(R/'ablation_without_scenario.csv',index=False)
    met=pd.DataFrame(allmetrics);met.to_csv(R/'metrics.csv',index=False)
    pd.concat(predictions).to_csv(A/'predictions.csv',index=False)
    ss=pd.concat(sens,ignore_index=True);ss.to_csv(R/'sensitivity_cases.csv',index=False)
    cc=pd.concat(curves,ignore_index=True);cc.to_csv(A/'sensitivity_grid.csv',index=False)
    agg=[]
    for (name,split),v in ss.groupby(['model','split']):
        agg.append({'model':name,'split':split,'cases':len(v),'median_delta_units_plus10':v.delta_units_plus10.median(),'median_factor_plus10':v.factor_plus10.median(),**{c+'_count':int(v[c].sum()) for c in ['any_increase_with_price','increase_at_plus10','flat_response','near_zero_denominator','large_response','large_factor','negative_raw_any','any_outside_product_support']}})
    pd.DataFrame(agg).to_csv(R/'sensitivity_summary.csv',index=False)
    cat=ss.groupby(['model','split','category']).agg(cases=('case_id','size'),median_factor_plus10=('factor_plus10','median'),increasing_fraction=('any_increase_with_price','mean'),flat_fraction=('flat_response','mean'),large_fraction=('large_response','mean')).reset_index();cat.to_csv(R/'sensitivity_by_category.csv',index=False)
    errors=[]
    for (name,split,category),v in pd.concat(predictions).groupby(['model','split','category']):errors.append({'model':name,'split':split,'category':category,'n':len(v),**metrics(v.actual,v.prediction)})
    pd.DataFrame(errors).to_csv(R/'errors_by_category.csv',index=False)
    ranking=met[met.split=='validation_available'].sort_values(['MAE','RMSE','model']);winner=ranking.iloc[0].model
    joblib.dump({'name':winner,'estimator':estimators[winner],'features':FEATURES,'config':CONFIG,'status':'experimental_not_approved_for_pricing'},A/'predictive_candidate.joblib')
    # Exemplos determinados por maior volume de TREINO por produto, sem escolher formato da curva.
    top=train.groupby('entity_id').fit_units.sum().sort_values(ascending=False).head(6).index
    examples=full[full.split=='test'].sort_values('week').drop_duplicates('entity_id');examples=examples[examples.entity_id.isin(top)]
    if len(examples)<6:examples=pd.concat([examples,full[full.split=='test'].sort_values(['week','entity_id']).drop_duplicates('entity_id')]).drop_duplicates('entity_id').head(6)
    fig,axs=plt.subplots(2,3,figsize=(15,8))
    for ax,(idx,v) in zip(axs.flat,examples.iterrows()):
        for name in estimators:
            c=cc[(cc.model==name)&(cc.case_id==idx)].sort_values('scale')
            ax.plot((c.scale-1)*100,c.prediction,marker='o',label=name)
        ax.set_title(v.entity_id[:8]+' / '+str(v.week.date()));ax.set_xlabel('Alteração do preço (%)');ax.set_ylabel('Unidades previstas');ax.grid(alpha=.2)
    axs.flat[0].legend(fontsize=7);fig.suptitle('Histórico fixo: somente o preço de cenário varia');fig.tight_layout();fig.savefig(R/'figures/sensitivity_examples.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,5))
    for ax,split in zip(axs,['validation','test']):
        vals=[];names=[]
        for name in estimators:
            v=ss[(ss.model==name)&(ss.split==split)].factor_plus10.dropna();vals.append(v.to_numpy());names.append(name)
        ax.boxplot(vals,tick_labels=names,showfliers=False);ax.axhline(1,color='black',linestyle='--');ax.tick_params(axis='x',rotation=35);ax.set_title(split);ax.set_ylabel('Fator q(+10% preço) / q(preço atual)')
    fig.tight_layout();fig.savefig(R/'figures/response_factors.png',dpi=150);plt.close(fig)
    audit={'protected_files_unchanged':protected_files()==before,'protected_files_count':len(before),'scenario_only_changes_checked':True,'frozen_products':int(full.entity_id.nunique()),'train_products':int(train.entity_id.nunique()),'counts':counts,'cohorts':{name:{'rows':len(v),'products':int(v.entity_id.nunique()),'categories':int(v.category.nunique())} for name,v in [('train_available',train),('validation_available',available),('validation',full[full.split=='validation']),('test',full[full.split=='test'])]},'predictive_candidate':winner,'elasticity':loglog['beta'],'elasticity_bootstrap_interval':loglog['cluster_bootstrap_95pct']}
    assert audit['protected_files_unchanged']
    (A/'parameters.json').write_text(json.dumps(params,indent=2,default=str))
    (A/'summary.json').write_text(json.dumps(audit,indent=2))
    (A/'manifest.json').write_text(json.dumps({'script_sha256':sha(Path(__file__)),'python':platform.python_version(),'raw_sha256':{p.name:sha(p) for p in (ROOT/'data/raw').glob('*.csv')},'features_sha256':sha(ROOT/'data/processed/product_week_features.csv'),'selection_sha256':sha(ROOT/'artifacts/selection.json')},indent=2))
    print(json.dumps(audit,indent=2));print(met.to_string(index=False));print(pd.DataFrame(agg).to_string(index=False))
if __name__=='__main__':run()
