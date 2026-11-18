# Etapa 2B — Validação temporal complementar

Este experimento adiciona validação temporal e busca de hiperparâmetros sem modificar `scripts/`, `reports/`, `artifacts/` ou `data/processed/`. O MovingAverage4 continua sendo o modelo selecionado no experimento original.

## Protocolo

Os quatro folds são expansivos e particionam semanas completas:

| Fold | Treino disponível antes de | Validação | Corte de disponibilidade dos rótulos |
|---|---|---|---|
| 1 | 2018-01-01 | 2018-01-01 a 2018-01-28 | 2018-01-29 |
| 2 | 2018-01-29 | 2018-01-29 a 2018-02-25 | 2018-02-26 |
| 3 | 2018-02-26 | 2018-02-26 a 2018-03-25 | 2018-03-26 |
| 4 | 2018-03-26 | 2018-03-26 a 2018-04-29 | 2018-05-01 |

Cada treino usa entregas confirmadas antes de sua origem; cada validação usa apenas entregas confirmadas antes do corte da próxima origem. O alvo medido é a contagem confirmada até o corte. Uma entidade-semana sem compras tem rótulo zero conhecido. Se houve compras, mas nem todos os itens têm confirmação de entrega, a contagem é marcada como `censored_lower_bound`: é um limite inferior, não zero de demanda eventual. Essa flag é exportada separadamente e impede interpretar esses casos como zeros estruturais. Semanas que ainda não terminaram no corte são excluídas. A semana que começa em 2018-04-30 continua excluída pela regra original.

A seleção usa a média do MAE de validação entre folds; RMSE médio desempata. MAE, RMSE, R², número de zeros conhecidos e rótulos censurados são exportados por modelo, parâmetros, nível, fold e partição, com dispersão das métricas no ranking. R² fica indefinido quando não há variância no rótulo. Como os limites inferiores censurados participam da métrica, os resultados medem previsões de confirmações até cada corte, não demanda eventual.

## Busca

- RandomForest: até 8 combinações amostradas deterministicamente (semente 42) para número de árvores, profundidade, mínimo de amostras por folha e `max_features`.
- GradientBoosting: até 8 combinações deterministicamente amostradas para estimadores, taxa de aprendizado, profundidade e mínimo por folha.
- Polynomial: graus 1 e 2.
- Linear, PreviousWeek e MovingAverage4: referências fixas.

Os pipelines existentes mantêm imputação, escala e one-hot; cada pipeline é ajustado novamente somente nas linhas de treino de cada fold. O conjunto retrospectivo de maio a agosto de 2018 não participa dos folds, do ajuste, do ranking ou das exportações.

## Execução e saídas

Na raiz do repositório, com as dependências científicas existentes e os CSVs brutos locais disponíveis:

```bash
python3.12 -m experiments.temporal_cv.experiment
```

A busca completa é deliberadamente executada apenas sob demanda. Primeiro faz a checagem de cobertura dos rótulos; se algum fold não tiver rótulos completos de treino ou validação, interrompe antes de ajustar modelos. Ela grava em `experiments/temporal_cv/results/` os arquivos `label_coverage.csv`, `fold_metrics.csv`, `fold_predictions.csv`, `candidate_ranking.csv`, `summary.json` e `report.md`. Não baixa dados nem altera os artefatos do benchmark original.

O teste retrospectivo já foi examinado no estudo original. Ele permanece isolado da seleção, mas não pode ser chamado de holdout cego; uma estimativa independente exigiria dados temporais ainda não inspecionados.
