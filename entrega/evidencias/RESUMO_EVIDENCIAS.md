# Resumo de evidências — PROJAPA, Tema 7

Preparado em 2026-11-17. Os PNGs foram gerados e copiados a partir dos artefatos disponíveis, sem retreinar modelos, alterar resultados ou copiar datasets/modelos/CSV grande. As métricas dos experimentos original e complementar têm alvos diferentes e não devem ser misturadas.

## Figuras disponíveis

Pasta `entrega/evidencias/figuras/`: 17 PNGs, cerca de 2 MB. Dez figuras novas e sete cópias pequenas das figuras que já existiam em `reports/` e `reports/price_response/`.

| Figura | Uso recomendado |
|---|---|
| [`original_teste_real_vs_previsto.png`](figuras/original_teste_real_vs_previsto.png) | Original: valores reais eventuais versus previstos do MovingAverage4 no teste produto-semana. |
| [`original_teste_residuos_no_tempo.png`](figuras/original_teste_residuos_no_tempo.png) | Original: resíduo real − previsto por semana; média e desvio-padrão entre produtos. |
| [`original_teste_distribuicao_residuos.png`](figuras/original_teste_distribuicao_residuos.png) | Original: distribuição dos resíduos no teste. |
| [`original_mae_seis_modelos_teste_eventual.png`](figuras/original_mae_seis_modelos_teste_eventual.png) | Original: seis modelos, alvo eventual no teste; produto e categoria em painéis separados. |
| [`complementar_mae_melhor_candidato_quatro_folds.png`](figuras/complementar_mae_melhor_candidato_quatro_folds.png) | Complementar: MAE médio e dispersão nos quatro folds; melhor configuração por família. |
| [`complementar_cobertura_rotulos_censurados.png`](figuras/complementar_cobertura_rotulos_censurados.png) | Complementar: cobertura de rótulos conhecidos/completos/censurados por fold. |
| [`eda_distribuicao_alvo_produto_semana_treino.png`](figuras/eda_distribuicao_alvo_produto_semana_treino.png) | EDA: alvo eventual do painel de treino produto-semana. |
| [`eda_distribuicao_precos_historicos_treino.png`](figuras/eda_distribuicao_precos_historicos_treino.png) | EDA: preços de itens entregues dos produtos elegíveis em 2017. |
| [`eda_vendas_por_categoria_olist.png`](figuras/eda_vendas_por_categoria_olist.png) | EDA: quantidade de itens entregues por categoria, top 15. |
| [`eda_correlacao_features_numericas_treino.png`](figuras/eda_correlacao_features_numericas_treino.png) | EDA: correlação de Pearson das features numéricas no treino. |
| [`original_existente_product_mae.png`](figuras/original_existente_product_mae.png) | Figura original existente: MAE produto-semana. |
| [`original_existente_product_weekly.png`](figuras/original_existente_product_weekly.png) | Figura original existente: série semanal de produto. |
| [`original_existente_category_mae.png`](figuras/original_existente_category_mae.png) | Figura original existente: MAE categoria-semana auxiliar. |
| [`original_existente_category_weekly.png`](figuras/original_existente_category_weekly.png) | Figura original existente: série semanal de categoria. |
| [`preco_existente_response_factors.png`](figuras/preco_existente_response_factors.png) | Figura existente: fatores de resposta no estudo observacional de preço. |
| [`preco_existente_sensitivity_examples.png`](figuras/preco_existente_sensitivity_examples.png) | Figura existente: cenários de sensibilidade a preço. |
| [`preco_existente_category_slopes.png`](figuras/preco_existente_category_slopes.png) | Figura existente: inclinações por categoria no estudo observacional de preço. |


### Filtros e fontes da EDA

| Figura | Dados e filtros | Período/amostra |
|---|---|---|
| `eda_distribuicao_alvo_produto_semana_treino.png` | `artifacts/product/predictions.csv`, MovingAverage4, `split=train`, `target_units` eventual; universo de IDs fixado em `artifacts/selection.json`. | 136 produtos, semanas 30/01–25/12/2017 após aquecimento; n=6.528 produto-semanas. Histograma em frequência logarítmica pela massa de zeros. |
| `eda_distribuicao_precos_historicos_treino.png` | Olist `order_items` + `orders` + `products`; apenas entregues, preço positivo e 136 produtos selecionados. Cada linha é item entregue. | Compras 30/01–31/12/2017; n=7.625 itens; mediana R$ 70,97; P95 R$ 235,90. Eixo de preço logarítmico. |
| `eda_vendas_por_categoria_olist.png` | Olist `order_items` + `orders` + `products`; status entregue, categoria ausente como `sem_categoria`; 15 categorias mais vendidas. | Período observado efetivo 15/09/2016–29/08/2018; n=110.197 linhas de item entregue. |
| `eda_correlacao_features_numericas_treino.png` | `data/processed/product_week_features.csv`; apenas treino e `history_weeks>=4`; Pearson por pares completos, sem imputação. Exclui target e rótulos. | n=6.528; features de lags/médias/desvio de unidades, atividade e tempo sem venda, preço, frete, categoria e índice temporal. |

## Resultados científicos confirmados

### Base e experimento original

Fonte: `reports/metricas.json`, `reports/modelagem.md`, `artifacts/run_summary.json`, `artifacts/selection.json` e `reports/model_metrics.csv`. A auditoria da Olist registra 99.441 pedidos, 112.650 linhas de item, 32.951 produtos no catálogo, 73 categorias/valores no catálogo, 96.478 pedidos entregues e 110.197 itens entregues. Compras totais no inventário: 04/09/2016–17/10/2018. O painel final usa **136 produtos** e **14 categorias auxiliares**. A análise exploratória mais ampla identificou 18 categorias elegíveis; não confundir essa contagem com as 14 usadas no painel final.

Divisão cronológica original, após quatro semanas de aquecimento: treino 2017 (48 semanas; produto n=6.528, categoria n=672), validação 01/01–23/04/2018 (17 semanas; n=2.312 e n=238), teste retrospectivo 07/05–20/08/2018 (16 semanas; n=2.176 e n=224). A semana 30/04–06/05 foi excluída como fronteira.

Foram comparados PreviousWeek, MovingAverage4, Linear, Polynomial, RandomForest e GradientBoosting. A seleção do campeão produto usou MAE da validação com rótulos disponíveis até 01/05/2018, RMSE como desempate e ordenação determinística. **MovingAverage4 permanece selecionado** (MAE=0,8007; RMSE=1,8374 nessa validação). A categoria é auxiliar; sua seleção foi Linear (MAE=34,8061; RMSE=48,3010), sem alterar o campeão de produto.

#### Teste original retrospectivo — alvo eventual

Valores lidos de `reports/model_metrics.csv` (`split=test`, `label=eventual`), em unidades por entidade-semana. O teste não foi critério de escolha.

| Modelo | Produto n | MAE | RMSE | R² | Categoria n | MAE | RMSE | R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MovingAverage4 | 2,176 | 0.5381 | 1.9778 | 0.0169 | 224 | 37.8460 | 50.5293 | 0.1690 |
| PreviousWeek | 2,176 | 0.5207 | 2.0509 | -0.0571 | 224 | 79.4643 | 94.2668 | -1.8921 |
| Linear | 2,176 | 0.8456 | 1.9867 | 0.0081 | 224 | 43.5983 | 53.4178 | 0.0713 |
| Polynomial | 2,176 | 0.5253 | 2.0628 | -0.0693 | 224 | 90.7098 | 106.3057 | -2.6779 |
| RandomForest | 2,176 | 0.8825 | 1.8749 | 0.1165 | 224 | 47.1911 | 64.4750 | -0.3529 |
| GradientBoosting | 2,176 | 0.8764 | 1.8792 | 0.1125 | 224 | 39.5771 | 51.8831 | 0.1239 |


No teste de produto, MovingAverage4: MAE=0,5381, RMSE=1,9778, R²=0,0169; 81,4% das 2.176 observações são zeros. PreviousWeek teve MAE=0,5207 no teste, mas esse resultado retrospectivo não altera a seleção feita na validação.

#### Ranking da seleção original — validação com rótulos disponíveis

| Modelo | Produto MAE | Produto RMSE | Categoria MAE | Categoria RMSE |
|---|---:|---:|---:|---:|
| MovingAverage4 | 0.8007 | 1.8374 | 48.9244 | 61.0816 |
| PreviousWeek | 0.9239 | 2.3077 | 82.9580 | 97.8527 |
| Linear | 0.9557 | 1.7822 | 34.8061 | 48.3010 |
| Polynomial | 0.9213 | 2.3066 | 87.3692 | 102.5486 |
| RandomForest | 0.9367 | 1.8324 | 58.3375 | 76.7763 |
| GradientBoosting | 0.9944 | 1.8114 | 46.4875 | 62.2368 |


Na validação original, havia 107 produto-semanas e 123 categoria-semanas em que o alvo eventual excedeu as entregas confirmadas até o corte; diferenças de volume: 267 e 2.123 unidades, respectivamente (`artifacts/product/predictions.csv`, `artifacts/category/predictions.csv`).

### Experimento complementar — quatro folds

Fontes: `experiments/temporal_cv/results/summary.json`, `candidate_ranking.csv`, `fold_metrics.csv` e `label_coverage.csv`. Folds expansivos: F1 com corte 29/01/2018; F2 26/02; F3 26/03; F4 01/05. Seleção por MAE médio, RMSE como desempate. Abaixo, melhor configuração de cada família pelo MAE médio, MAE, RMSE e R² por fold e métricas agregadas. Estes valores medem erros contra **entregas confirmadas até cada corte**; rótulos censurados são limites inferiores, não demanda eventual.

### Produto-semana

| Família (melhor configuração por MAE) | Parâmetros | F1 (MAE / RMSE / R²) | F2 (MAE / RMSE / R²) | F3 (MAE / RMSE / R²) | F4 (MAE / RMSE / R²) | Média ± DP (MAE / RMSE / R²) |
|---|---|---:|---:|---:|---:|---:|
| PreviousWeek | `referência fixa` | 0.555 / 1.484 / -0.129 | 0.557 / 1.709 / -0.094 | 0.469 / 1.391 / -0.116 | 0.526 / 1.508 / -0.137 | MAE 0.527±0.041; RMSE 1.523±0.134; R² -0.119±0.019 |
| MovingAverage4 | `referência fixa` | 0.666 / 1.339 / 0.081 | 0.634 / 1.450 / 0.213 | 0.532 / 1.093 / 0.311 | 0.514 / 1.173 / 0.312 | MAE 0.587±0.075; RMSE 1.264±0.161; R² 0.229±0.109 |
| GradientBoosting | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":150}` | 0.686 / 1.410 / -0.020 | 0.706 / 1.444 / 0.218 | 0.669 / 1.219 / 0.143 | 0.594 / 1.187 / 0.296 | MAE 0.664±0.049; RMSE 1.315±0.131; R² 0.159±0.135 |
| Polynomial | `{"preprocess__num__poly__degree":2}` | 0.527 / 1.436 / -0.058 | 0.537 / 1.584 / 0.060 | 1.130 / 1.590 / -0.459 | 0.515 / 1.421 / -0.009 | MAE 0.677±0.302; RMSE 1.508±0.092; R² -0.116±0.233 |
| RandomForest | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":10,"regressor__n_estimators":200}` | 0.773 / 1.441 / -0.065 | 0.677 / 1.416 / 0.249 | 0.648 / 1.209 / 0.158 | 0.621 / 1.196 / 0.284 | MAE 0.680±0.066; RMSE 1.316±0.131; R² 0.156±0.157 |
| Linear | `referência fixa` | 1.057 / 1.514 / -0.176 | 0.703 / 1.450 / 0.212 | 0.702 / 1.208 / 0.159 | 0.625 / 1.216 / 0.261 | MAE 0.772±0.193; RMSE 1.347±0.158; R² 0.114±0.198 |

### Categoria-semana

| Família (melhor configuração por MAE) | Parâmetros | F1 (MAE / RMSE / R²) | F2 (MAE / RMSE / R²) | F3 (MAE / RMSE / R²) | F4 (MAE / RMSE / R²) | Média ± DP (MAE / RMSE / R²) |
|---|---|---:|---:|---:|---:|---:|
| MovingAverage4 | `referência fixa` | 28.188 / 37.202 / 0.050 | 27.188 / 37.263 / 0.279 | 26.237 / 34.947 / 0.256 | 32.182 / 39.233 / 0.202 | MAE 28.448±2.613; RMSE 37.161±1.752; R² 0.197±0.103 |
| GradientBoosting | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":100}` | 29.687 / 37.450 / 0.037 | 29.565 / 39.167 / 0.203 | 26.550 / 36.553 / 0.186 | 30.688 / 37.801 / 0.260 | MAE 29.122±1.787; RMSE 37.743±1.085; R² 0.172±0.095 |
| Linear | `referência fixa` | 38.189 / 48.428 / -0.610 | 30.246 / 38.855 / 0.216 | 27.199 / 37.497 / 0.144 | 25.510 / 33.920 / 0.404 | MAE 30.286±5.621; RMSE 39.675±6.196; R² 0.038±0.446 |
| Polynomial | `{"preprocess__num__poly__degree":1}` | 38.189 / 48.428 / -0.610 | 30.246 / 38.855 / 0.216 | 27.199 / 37.497 / 0.144 | 25.510 / 33.920 / 0.404 | MAE 30.286±5.621; RMSE 39.675±6.196; R² 0.038±0.446 |
| RandomForest | `{"regressor__max_depth":null,"regressor__max_features":0.5,"regressor__min_samples_leaf":10,"regressor__n_estimators":400}` | 34.928 / 43.991 / -0.328 | 33.578 / 41.487 / 0.106 | 27.614 / 38.481 / 0.098 | 34.104 / 43.088 / 0.038 | MAE 32.556±3.341; RMSE 41.762±2.420; R² -0.022±0.207 |
| PreviousWeek | `referência fixa` | 43.446 / 57.129 / -1.240 | 40.161 / 57.871 / -0.740 | 40.036 / 55.826 / -0.898 | 58.457 / 71.975 / -1.684 | MAE 45.525±8.765; RMSE 60.700±7.564; R² -1.141±0.418 |
O menor MAE médio em produto foi PreviousWeek (0,5268 ± 0,0412); MovingAverage4 teve 0,5866 ± 0,0748. Em categoria, MovingAverage4 teve 28,4484 ± 2,6135, mas 238/238 observações de validação são censuradas; não representa avaliação de demanda eventual e não substitui o modelo original.

| Rótulos nas validações dos quatro folds | Total | Zero conhecido | Positivo completo | Censurado |
|---|---:|---:|---:|---:|
| Produto-semana | 2,312 | 1,513 | 312 | 487 |
| Categoria-semana | 238 | 0 | 0 | 238 |

As janelas de validação dos folds não se sobrepõem. Contagens são observações entidade-semana, não unidades vendidas.

## Limitações científicas

- O painel semanal é esparso (densidade de 2,81% em produto-semana; `reports/metricas.json`). Sem venda observada não prova demanda zero, falta de estoque ou indisponibilidade.
- A elegibilidade privilegia itens recorrentes no treino, não produtos novos; a categoria é estática.
- Há atraso de confirmação e rótulos censurados, especialmente em categoria no experimento complementar (100% da validação).
- O teste original é retrospectivo e já foi examinado, não é holdout cego. Zeros e mudança temporal afetam métricas e extrapolação.
- A resposta ao preço é observacional: preço realizado é proxy de transação sujeito a seleção/simultaneidade, sem validação causal. Não há dados completos de estoque, custos, concorrentes ou ofertas contínuas. `reports/price_response.md` considera o motor experimental e não valida uma curva confiável por produto.

## Evidências do sistema e validações

- **FastAPI:** contratos e rotas em `pricing/api.py` e `pricing/schemas.py`: health, metadados, catálogo, histórico e CRUD de simulações.
- **Streamlit:** `pricing/ui.py`; chama a API via `PRICING_API_URL`.
- **SQLite:** `pricing/storage.py`; Compose monta volume em `/app/runtime`. A simulação e persistência local isolada foram testadas em banco temporário, sem alterar o banco original.
- **Docker Compose:** `compose.yaml` define API, UI e healthchecks. O usuário informou HTTP 200 para ambos; o Codex não acessa o socket/portas nesta sessão, sem captura independente.
- **MLflow:** banco local `mlruns/mlflow.db` consultado nesta etapa: 43 runs (1 pai + 42 candidatos), `record_type=retrospective_import`, seed 42, commit `9ccc7381e3662bba758d311047f0805083bcdd06`. As versões registradas são do ambiente importador. O banco é local/ignorado.
- **DVC:** `dvc.yaml` configura o estágio `temporal_cv`; `dvc repro` não foi executado, `dvc.lock` não existe. Não afirmar reprodução integral.
- **GitHub Actions:** execução hospedada bloqueada por cobrança, segundo o estado informado; CI não aprovada.

### Capturas manuais pendentes

1. Terminal Ubuntu: `sudo docker compose -p projapa-etapa4 ps` com API/UI `healthy`, e respostas HTTP 200 de `/health` e `/_stcore/health`.
2. Swagger `http://localhost:8000/docs`: POST com resposta 201/ID e GET da simulação.
3. Dashboard `http://localhost:8501`: resultado da simulação e tela Histórico com a mesma ID.
4. Terminal: consulta da simulação antes e depois de `sudo docker compose -p projapa-etapa4 restart api`; não apagar o volume.
5. MLflow UI local: experimento com 42 runs filhos e detalhes mostrando tags, seed, commit, parâmetros e métricas.
6. Terminal com `DVC_SITE_CACHE_DIR=/tmp/projapa-dvc-site-cache dvc dag`; isso demonstra o DAG configurado, não execução.
7. Se for necessário anexar a pendência de CI, tela GitHub Actions do bloqueio por cobrança; não é evidência de aprovação.

### Testes e arquivos para o LaTeX

Testes científicos: 17 aprovados com `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`. Testes MVP: 41 coletados; 24 passaram, depois a suíte atingiu timeout de 60 s em `test_api_lifecycle_and_persistence` (TestClient), sem falha de asserção anterior. Não declarar a suíte completa aprovada. Sem commit/push.

Envie para finalizar o LaTeX: `entrega/evidencias/` (este resumo e PNGs), `reports/modelagem.md`, `reports/price_response.md`, `reports/metricas.json`, `reports/model_metrics.csv`, `artifacts/run_summary.json`, `artifacts/selection.json`, os resultados compactos `experiments/temporal_cv/results/summary.json`, `candidate_ranking.csv`, `fold_metrics.csv`, `label_coverage.csv` e `report.md`, `experiments/temporal_cv/MLOPS.md`, `dvc.yaml`, `compose.yaml`, `Dockerfile`, `.github/workflows/tests.yml` e capturas manuais. Não envie CSVs brutos da Olist, modelos `.joblib`, o banco local `mlruns/mlflow.db` ou o CSV `fold_predictions.csv` (~253 MB); os resumos compactos bastam.
