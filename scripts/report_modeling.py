"""Gera o relatório somente a partir das saídas efetivamente calculadas."""
from pathlib import Path
import json
import pandas as pd
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'artifacts/run_summary.json').read_text())
m=pd.read_csv(R/'reports/model_metrics.csv')

def table(df):
    cols=list(df.columns)
    def f(v):
        if isinstance(v,float):return f'{v:.4f}'
        return str(v)
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(f(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))

features=[
('category','Categoria estática do produto, obtida em registros de treino; one-hot aprendido no treino.'),
('units_lag_1 / 2 / 4','Itens comprados 1, 2 ou 4 semanas antes, com entrega confirmada antes da previsão.'),
('units_mean_4w / units_std_4w','Média e desvio populacional dessas contagens nas quatro semanas anteriores.'),
('active_weeks_8w','Semanas anteriores com entrega já conhecida de alguma compra daquela semana.'),
('weeks_since_last_sale','Distância à semana da última compra cuja entrega já era conhecida.'),
('last_observed_price','Mediana da última semana com transações entregues já conhecidas; não é oferta atual.'),
('price_age_weeks','Distância à semana desse preço histórico.'),
('price_missing','Ausência de preço histórico disponível; não indica ausência de oferta.'),
('price_change_last_observed','Variação relativa entre as duas últimas medianas semanais disponíveis.'),
('freight_median_lag','Mediana de frete das compras das quatro semanas anteriores já entregues.'),
('sellers_count_4w','Vendedores dessas transações nas quatro semanas anteriores.'),
('category_units_lag_1 / category_units_mean_4w','Contexto da categoria: contagem anterior e média de quatro semanas, sob o mesmo corte de disponibilidade.'),
('week_sin / week_cos','Calendário da semana a prever, conhecido previamente; periodicidade de 52,18 semanas.'),
('time_index / history_weeks','Semanas desde o começo fixo do painel. Redundantes neste recorte; documentadas como limitação da especificação inicial.')]
parts=['# Modelagem — Motor de Precificação Dinâmica para Marketplace\n\nDupla: **Danylo e William**. Execução real em 19/09/2026. Experimento principal produto-semana; categoria-semana auxiliar. Não foram implementados API, interface ou motor de preços.\n',
'''## Definição do alvo e disponibilidade temporal

O alvo `target_units` **continua sendo o número de itens de pedidos que terminaram entregues, agrupados pela semana da compra**. Não foi trocado por valor monetário, preço, total de pedidos de qualquer status ou quantidade de entregas realizadas naquela semana.

Há, porém, uma diferença obrigatória entre o alvo eventual e aquilo que era conhecido na data histórica. O CSV contém status final e data de entrega. Não é possível usar uma entrega futura para construir atributos passados nem treinar em janeiro com confirmações de fevereiro. Por isso:

- `target_units` preserva a contagem eventual e é usado somente para avaliação retrospectiva.
- `label_available_train` conta, para cada semana de compra, apenas itens entregues antes de **01/01/2018**. É o rótulo efetivamente usado no ajuste.
- `label_available_selection` conta apenas entregas anteriores a **01/05/2018**. É o rótulo de validação utilizado para selecionar o campeão.
- Esses dois rótulos são observações **censuradas à direita do mesmo alvo**, não alvos perfeitamente completos. A diferença é quantificada abaixo. Isso impõe viés, sobretudo nas semanas próximas aos cortes; não foi ocultado nem corrigido usando futuro.
- Na avaliação retrospectiva de validação e teste, os resultados entregues posteriormente podem ser usados como verdade de referência, mas nunca são fornecidos ao ajuste ou à decisão de qual modelo salvar.

As métricas principais abaixo usam o alvo eventual. As métricas com rótulo disponível são salvas separadamente e apresentadas para a seleção. Não alegamos uma comparação operacional sem censura. Uma extensão metodológica poderá definir explicitamente um alvo de horizonte fixo de confirmação ou uma política de maturação, exigindo nova versão do experimento.

## Construção e seleção

O pipeline parte dos CSVs de pedidos, itens e produtos. Itens são unidades, e não a soma do identificador sequencial `order_item_id`. Junções muitos-para-um são verificadas. Categoria estática é uma hipótese: o catálogo não possui histórico de versões.

Produtos: pelo menos 20 pedidos, 8 semanas com venda e 2 preços distintos nas compras de 2017, **com entregas conhecidas antes de janeiro de 2018**. Categorias auxiliares: pelo menos 90% de semanas com vendas e mediana de 20 unidades/semana, somente no treino e com o mesmo corte de confirmação. Nenhum filtro depende de validação/teste.
''']
parts.append(f"Resultado: **{s['product']['entities']} produtos**, contra os 149 da auditoria retrospectiva anterior. A diferença decorre do corte de confirmação, não de uma busca por desempenho. O experimento auxiliar inclui **{s['category']['entities']} categorias**.\n")
parts.append('''
O painel é preenchido em todas as semanas, mesmo sem transação. Zero significa **nenhum item entregue registrado para aquela semana de compra na versão avaliada**, não estoque disponível nem demanda latente zero. `availability_state=unknown` documenta isso. Preço ausente não é preenchido com preço futuro. O último preço conhecido tem idade e sinalizador explícitos; imputação mediana é ajustada no treino. Não se cria estoque, concorrência ou custo.

Há quatro semanas iniciais de aquecimento, excluídas para todos os métodos. O catálogo elegível é fixado ao final de 2017, e as features anteriores são reconstruídas ponto no tempo. Trata-se de um benchmark retrospectivo com universo escolhido no treino, não da simulação de um catálogo que já era conhecido em janeiro de 2017.

## Features e exclusões

São **19 features numéricas e uma categórica**, idênticas entre os quatro modelos, com expansão de grau 2 apenas nas numéricas da regressão polinomial. `entity_id`, alvos, flags de avaliação, datas máximas de origem e status de disponibilidade não entram no modelo. Categoria não é convertida em número ordinal.
''')
parts.append(table(pd.DataFrame(features,columns=['Feature','Definição / disponibilidade'])))
parts.append('''
Todas as variáveis transacionais usam `purchase < week_start` e `delivery < week_start`. Até os preços são extraídos somente desse subconjunto confirmado: é uma política conservadora, que evita depender do status final futuro. Calendário da semana-alvo é conhecido antecipadamente e não usa transações daquela semana.

## Divisão temporal

Semanas de segunda a domingo. A semana de **30/04–06/05/2018** atravessa o corte e fica excluída como amostra supervisionada, evitando classificar compras de maio como validação. Ela pode compor histórico de previsões seguintes depois que suas transações se tornam disponíveis. A semana parcial final de agosto não entra. Treino permanece em 2017, validação em janeiro–abril e teste em maio–agosto.

Avaliação rolling-origin de um passo: a cada semana, pode-se incorporar histórico já disponível de semanas anteriores de validação/teste; os parâmetros e transformações ficam congelados no treino. Isso não equivale a prever quatro meses de uma só vez.
''')
for level in ['product','category']:
    parts.append(f'\n### {level}\n')
    df=pd.DataFrame([{'split':k,**v} for k,v in s[level]['splits'].items()])
    parts.append(table(df))
parts.append('''
`available_label_units` quantifica quanto do alvo já estava confirmado no corte. `zero_fraction` é a proporção de células sem venda registrada no alvo eventual. Datas da tabela representam o início da primeira e da última semana de cada conjunto.

## Referências, modelos e comparação justa

- **PreviousWeek**: contagem disponível da semana de compra anterior. O atraso de confirmação pode subestimar vendas recentes.
- **MovingAverage4**: média disponível das quatro semanas anteriores.
- **Linear**: regressão linear, numéricas padronizadas e categoria one-hot.
- **Polynomial**: regressão linear sobre termos numéricos de grau 2, com padronização; categoria one-hot sem expansão polinomial. Sem busca de graus.
- **RandomForest**: 200 árvores, profundidade máxima 8, mínimo 5 amostras por folha, semente 42.
- **GradientBoosting**: 150 árvores, taxa 0,05, profundidade 2, mínimo 10 amostras por folha, perda quadrática, semente 42.

Mesmas linhas, features e rótulos para os quatro modelos; baselines usam o mesmo histórico disponível. Imputação e codificação são aprendidas somente no treino. Predições negativas são truncadas em zero para todos; quantidades esperadas não são arredondadas. Sem tuning, sem retreino em validação, sem refit final. MAE é o critério primário; RMSE e nome desempatam. Baselines participam da escolha: um modelo complexo não é automaticamente campeão.

## Resultados retrospectivos reais

MAE e RMSE em unidades por entidade-semana. R² pode ser negativo e não é definido em grupos constantes; nesses grupos fica vazio nos CSVs.
''')
for level in ['product','category']:
    parts.append(f'\n### {level}: validação e teste, alvo eventual\n')
    v=m[(m.level==level)&(m.label=='eventual')&m.split.isin(['validation','test'])]
    parts.append(table(v[['model','split','n','MAE','RMSE','R2']]))
    parts.append(f'\n![MAE {level}](figures/{level}_mae.png)\n')
    parts.append(f'\n### {level}: seleção com informação disponível em 01/05/2018\n')
    parts.append(table(pd.DataFrame(s[level]['selection_ranking'])))
    parts.append(f"\nCampeão: **{s[level]['winner']}**. Melhor entre os quatro modelos treinados: **{s[level]['best_ml']}**. Artefatos: `artifacts/{level}/chosen_model.joblib` e `best_ml_model.joblib`. O campeão contém configuração, lista de features, estimador ou regra de baseline e política de truncamento.\n")
    parts.append(f'\n![Série semanal {level}](figures/{level}_weekly.png)\n')
parts.append('''## Diagnóstico crítico da regressão polinomial

No produto-semana, **2.287 de 2.312 previsões de validação** e **todas as 2.176 de teste** foram negativas antes do truncamento. No teste, o modelo retorna zero em todas as linhas após a regra comum. No auxiliar, todas as 224 previsões de teste também são truncadas para zero. Isso é uma falha de extrapolação/generalização, não sucesso preditivo. A posição de Polynomial como melhor ML por MAE disponível no produto é favorecida pela abundância de zeros; o artefato `best_ml_model.joblib` preserva o experimento, mas **não é recomendado para uso**.

RandomForest por categoria apresenta MAE eventual de treino 11,14 contra 64,48 na validação: sinal forte de perda de generalização, compatível com overfitting e mudança temporal. O comportamento polinomial e as redundâncias de atributos deverão ser tratados em uma nova rodada pré-especificada; não ajustamos o experimento após observar o teste.

Na análise auxiliar, Linear é escolhido pela validação, mas a média móvel supera seu MAE no teste (37,85 contra 43,60). O campeão não foi trocado após ver o teste.

## Erros por produto, categoria e atividade
''')
for level in ['product','category']:
    winner=s[level]['winner']
    e=pd.read_csv(R/f'reports/{level}_errors_by_entity_id.csv')
    e=e[(e.model==winner)&(e.split=='test')].sort_values('MAE',ascending=False).head(5)
    parts.append(f'\nMaiores MAEs de teste do campeão {level}:\n'+table(e[['entity_id','n','actual_units','MAE','RMSE','R2']]))
    seg=pd.read_csv(R/f'reports/{level}_errors_by_activity.csv')
    seg=seg[(seg.model==winner)&(seg.split=='test')]
    parts.append('\nSemanas com e sem venda registrada:\n'+table(seg[['no_recorded_sale','n','MAE','RMSE','R2']]))
parts.append('''
CSV de erros de **todos os seis métodos**, separados por validação/teste: `product_errors_by_entity_id.csv`, `product_errors_by_category.csv`, `category_errors_by_entity_id.csv`, `category_errors_by_category.csv`. Eles incluem contagem de linhas, volume real, viés médio, MAE, RMSE e R². Erros segmentados por atividade evitam que o grande número de zeros esconda falhas nas semanas com vendas.

## Generalização e possíveis sinais de overfitting

A tabela abaixo usa a mesma verdade eventual no treino, validação e teste. O treino foi ajustado com rótulos disponíveis, portanto estes erros não são exatamente o objetivo minimizado pelo ajuste; os erros contra rótulos de treino estão também em `model_metrics.csv`.
''')
for level in ['product','category']:
    a=m[(m.level==level)&(m.label=='eventual')].pivot(index='model',columns='split',values='MAE').reset_index()
    parts.append(f'\n{level}:\n'+table(a))
    ml=s[level]['best_ml']
    row=a[a.model==ml].iloc[0]
    parts.append(f"\nPara {ml}, MAE de treino {row['train']:.4f}, validação {row['validation']:.4f} e teste {row['test']:.4f}. Diferenças devem ser interpretadas junto à queda/mudança no volume de vendas e à censura dos rótulos. Um teste melhor que o treino também pode refletir mais semanas sem transações, e não melhoria do modelo.\n")
parts.append('''
Comparar especialmente Polynomial e RandomForest entre treino e períodos posteriores: erro de treino baixo com piora fora dele é sinal compatível com overfitting. A expansão polinomial pode extrapolar mal no tempo, especialmente com atributos correlacionados (`time_index` e `history_weeks` são redundantes). Nenhum resultado de teste foi usado para alterar hiperparâmetros ou substituir o campeão.

## Limitações e recomendação

1. Previsão de vendas observadas não mede demanda latente, disponibilidade ou elasticidade causal. Não há base para concluir preço ótimo ou ganho real de receita.
2. Rótulos de treino/seleção têm atraso de confirmação explicitamente quantificado. Categorias e produtos possuem inatividade e possível saída do catálogo desconhecida. Entregas sem timestamp são excluídas das features disponíveis, embora possam estar no alvo retrospectivo.
3. O universo restrito favorece produtos recorrentes do treino, não produtos novos. Alterações do mix afetam o experimento auxiliar por categoria.
4. Mais acurácia agregada não garante bom desempenho em semanas com vendas ou em cada produto. Os CSVs segmentados devem orientar a próxima decisão.
5. Não há validação causal de preços, intervalos de previsão nem teste de significância entre modelos; há uma comparação temporal inicial de configuração fixa.

O próximo passo deve ser discutir estes resultados e a política de maturação antes de construir o motor de preços. O artefato salvo é um preditor experimental de vendas, não um precificador validado. Esta etapa termina aqui, sem FastAPI ou Streamlit.

## Reprodução e verificações

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-modeling.txt
.venv/bin/python scripts/modeling.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/report_modeling.py
```

Dependências congeladas; semente 42; hashes dos CSVs e do script em `artifacts/run_manifest.json`. Parâmetros completos em `artifacts/{product,category}/parameters.json`. Matrizes finais em `data/processed/{product,category}_week_features.csv`; métricas em `reports/model_metrics.csv` e `artifacts/{product,category}/metrics.csv`; previsões individuais em `artifacts/{product,category}/predictions.csv`.

Testes verificam: transações futuras não alteram features passadas; compra antiga com entrega futura não aparece no histórico; corte estrito de disponibilidade; exclusão de semana que cruza o corte; semântica explícita de zero e rótulo censurado. O pipeline verifica ainda datas máximas de origem e equivalência das previsões após salvar/recarregar o campeão. Logs reais em `artifacts/tests.log` e `artifacts/run.log`.
''')
(R/'reports/modelagem.md').write_text('\n'.join(parts),encoding='utf-8')
print('reports/modelagem.md gerado a partir dos artefatos executados.')
