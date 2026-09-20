"""Análise descritiva reproduzível; não treina modelos nem inventa exposição."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / 'data/raw', ROOT / 'reports'
OUT.mkdir(exist_ok=True)

def save(df, name):
    df.to_csv(OUT / name, index=False)

def summary(s):
    return s.describe(percentiles=[.25,.5,.75,.9,.95,.99]).to_dict()

tables = {p.stem: pd.read_csv(p) for p in sorted(RAW.glob('*.csv'))}
inventory = []
for name, df in tables.items():
    inventory.append({'table':name,'rows':len(df),'columns':len(df.columns),'duplicate_rows':int(df.duplicated().sum())})
save(pd.DataFrame(inventory), 'inventario.csv')
save(pd.DataFrame([{'table':n,'column':c,'missing':int(t[c].isna().sum()),'missing_pct':100*t[c].isna().mean()} for n,t in tables.items() for c in t]), 'qualidade_colunas.csv')
o = tables['olist_orders_dataset'].copy()
i = tables['olist_order_items_dataset'].copy()
p = tables['olist_products_dataset'].copy()
o['order_purchase_timestamp'] = pd.to_datetime(o['order_purchase_timestamp'])
assert o.order_id.is_unique and p.product_id.is_unique
assert not i.duplicated(['order_id','order_item_id']).any()
x = i.merge(o, on='order_id', how='left', validate='many_to_one', indicator=True)
missing_orders = int(x['_merge'].ne('both').sum())
x = x.drop(columns='_merge').merge(p[['product_id','product_category_name']],on='product_id',how='left',validate='many_to_one',indicator=True)
missing_products = int(x['_merge'].ne('both').sum())
x['category'] = x.product_category_name.fillna('sem_categoria')
x['date'] = x.order_purchase_timestamp.dt.normalize()
x['price_cents'] = (x.price * 100).round().astype('int64')
x['week'] = x['date'] - pd.to_timedelta(x['date'].dt.dayofweek,unit='D')
d = x[x.order_status.eq('delivered')].copy()
# Núcleo regular explícito: meses completos antes do término da cobertura principal.
a = d[d['date'].between('2017-01-01','2018-08-31')].copy()
products = d.groupby('product_id').agg(items=('order_id','size'),orders=('order_id','nunique'),sellers=('seller_id','nunique'),active_days=('date','nunique'),active_weeks=('week','nunique'),prices=('price_cents','nunique'),price_min=('price','min'),price_max=('price','max'),price_median=('price','median'),first=('date','min'),last=('date','max'))
products['span_days'] = (products['last']-products['first']).dt.days+1
products['active_day_density'] = products.active_days/products.span_days
products['price_range_pct'] = 100*(products.price_max/products.price_min-1)
save(products.reset_index(),'produtos.csv')
# Variação entre medianas diárias evita contar só diferenças simultâneas entre vendedores.
pday=d.groupby(['product_id','date']).agg(price=('price','median')).reset_index()
pday['price_cents']=(pday.price*100).round().astype('int64')
psday=d.groupby(['product_id','seller_id','date']).agg(price=('price','median')).reset_index()
psday['price_cents']=(psday.price*100).round().astype('int64')
timevariation=pday.groupby('product_id').agg(days=('date','size'),daily_prices=('price_cents','nunique'))
pairvariation=psday.groupby(['product_id','seller_id']).agg(days=('date','size'),daily_prices=('price_cents','nunique'))
pairvariation['varies_over_days']=(pairvariation.days>=2)&(pairvariation.daily_prices>=2)
save(pairvariation.reset_index(),'variacao_produto_vendedor.csv')
monthly=x.groupby(x.date.dt.to_period('M').astype(str)).agg(items=('order_id','size'),orders=('order_id','nunique'),products=('product_id','nunique'))
save(monthly.reset_index(),'cobertura_mensal.csv')
# Painéis preenchidos servem APENAS para densidade transacional, não exposição/estoque.
density=[]
for level in ['product_id','category']:
 for freq in ['day','week']:
  key='date' if freq=='day' else 'week'
  frame=a.copy()
  if freq=='week': frame=frame[frame.date.between('2017-01-02','2018-08-26')]
  dates=pd.date_range('2017-01-01','2018-08-31') if freq=='day' else pd.date_range('2017-01-02','2018-08-20',freq='7D')
  counts=frame.groupby([level,key]).size().unstack(fill_value=0).reindex(columns=dates,fill_value=0)
  vals=counts.to_numpy()
  density.append({'level':level,'period':freq,'entities':len(counts),'periods':len(dates),'cells':int(vals.size),'observed_cells':int((vals>0).sum()),'density_pct':float((vals>0).mean()*100),'median_units_positive':float(pd.Series(vals[vals>0]).median()),'median_active_periods_per_entity':float((counts>0).sum(axis=1).median())})
save(pd.DataFrame(density),'densidade.csv')
w=a[a.date.between('2017-01-02','2018-08-26')].copy()
weeks=pd.date_range('2017-01-02','2018-08-20',freq='7D')
agg=w.groupby(['category','week']).agg(units=('order_id','size'),orders=('order_id','nunique'),products=('product_id','nunique'),price_median=('price','median'),price_mean=('price','mean'))
idx=pd.MultiIndex.from_product([sorted(w.category.unique()),weeks],names=['category','week'])
panel=agg.reindex(idx).reset_index()
for c in ['units','orders','products']: panel[c]=panel[c].fillna(0).astype(int)
# Preserva preço ausente: preço sem venda não é observado.
panel.to_csv(ROOT/'data/processed/category_week_diagnostic.csv',index=False)
cat=panel.groupby('category').agg(units=('units','sum'),active_weeks=('units',lambda s:int(s.gt(0).sum())),median_units_week=('units','median'),p25_units_week=('units',lambda s:s.quantile(.25)))
cat['coverage_pct']=100*cat.active_weeks/len(weeks)
cat['eligible']=(cat.coverage_pct>=90)&(cat.median_units_week>=20)&cat.index.to_series().ne('sem_categoria')
save(cat.sort_values('units',ascending=False).reset_index(),'categorias.csv')
status=o.order_status.value_counts().to_dict()
stats={'inventory':inventory,'orders':len(o),'items':len(i),'products_catalog':len(p),'products_sold':int(i.product_id.nunique()),'categories_catalog':int(p.product_category_name.nunique()),'missing_category_catalog':int(p.product_category_name.isna().sum()),'sellers':int(i.seller_id.nunique()),'status':status,'purchase_min':str(o.order_purchase_timestamp.min()),'purchase_max':str(o.order_purchase_timestamp.max()),'unmatched_orders':missing_orders,'unmatched_products':missing_products,'nonpositive_prices':int(i.price.le(0).sum()),'negative_freight':int(i.freight_value.lt(0).sum()),'price_all':summary(i.price),'delivered_orders':int(d.order_id.nunique()),'delivered_items':len(d),'delivered_products':len(products),'single_sale_products':int(products['items'].eq(1).sum()),'products_multiple_prices':int(products.prices.gt(1).sum()),'products_multiple_days':int(timevariation.days.ge(2).sum()),'products_daily_price_variation':int(((timevariation.days>=2)&(timevariation.daily_prices>=2)).sum()),'product_seller_pairs':len(pairvariation),'pairs_multiple_days':int(pairvariation.days.ge(2).sum()),'pairs_daily_price_variation':int(pairvariation.varies_over_days.sum()),'products_with_pair_variation':int(pairvariation[pairvariation.varies_over_days].reset_index().product_id.nunique()),'product_items_distribution':summary(products['items']),'product_active_weeks_distribution':summary(products.active_weeks),'products_20_orders_8_weeks_2_prices':int(((products.orders>=20)&(products.active_weeks>=8)&(products.prices>=2)).sum()),'analysis_items':len(a),'analysis_orders':int(a.order_id.nunique()),'weekly_items':len(w),'weeks':len(weeks),'eligible_categories':int(cat.eligible.sum()),'eligible_units':int(cat.loc[cat.eligible,'units'].sum()),'density':density}
(OUT/'metricas.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(stats,indent=2,ensure_ascii=False))
print(cat.sort_values('units',ascending=False).head(20).to_string())
# Seleção de produtos somente em 2017, sem usar o futuro para elegibilidade.
train=w[w.week<'2018-01-01']
g=train.groupby('product_id').agg(orders=('order_id','nunique'),weeks=('week','nunique'),prices=('price_cents','nunique'))
eligible=g[(g.orders>=20)&(g.weeks>=8)&(g.prices>=2)]
subset=w[w.product_id.isin(eligible.index)]
save(eligible.reset_index(),'produtos_elegiveis_treino.csv')
supp={'training_cutoff':'2018-01-01','selected_products':len(eligible),'items':len(subset),'observed_product_weeks':subset.groupby(['product_id','week']).ngroups,'possible_product_weeks':len(eligible)*len(weeks),'density_pct':100*subset.groupby(['product_id','week']).ngroups/(len(eligible)*len(weeks)),'training_items':int(subset.week.lt('2018-01-01').sum()),'later_items':int(subset.week.ge('2018-01-01').sum()),'later_products':int(subset.loc[subset.week.ge('2018-01-01'),'product_id'].nunique())}
(OUT/'subconjunto_produtos.json').write_text(json.dumps(supp,indent=2),encoding='utf-8')
