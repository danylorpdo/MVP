# Pipeline local e reprodutibilidade

## Escopo e metodologias

O benchmark original continua congelado em `scripts/`, `artifacts/` e `reports/`; sua seleção atual segue sendo MovingAverage4. O experimento em `experiments/temporal_cv/` é complementar: usa quatro folds expansivos anteriores ao teste retrospectivo, com seleção por MAE médio e RMSE como desempate. Seus rótulos são entregas confirmadas até cada corte e podem ser limites inferiores censurados; portanto, não representam diretamente demanda eventual. Os resultados não devem ser misturados com as métricas retrospectivas do benchmark original.

## Etapas e rastreabilidade

| Etapa | Entradas | Saídas | Limitação atual |
|---|---|---|---|
| `temporal_cv` (DVC) | `experiments/temporal_cv/experiment.py`, `scripts/modeling.py`, `requirements-modeling.txt` e os três CSVs brutos de `data/raw/` | ranking, métricas por fold, cobertura dos rótulos, resumo e relatório em `experiments/temporal_cv/results/` | Os CSVs brutos são ignorados pelo Git e não são copiados nem armazenados pelo DVC; precisam estar disponíveis localmente. O estágio executa a busca completa somente quando solicitado. |
| Registro MLflow local | Resultados já existentes, `summary.json`, métricas, ranking e manifesto | Experimento `PROJAPA-temporal-cv-complementar` em `mlruns/mlflow.db`, com artefatos locais em `mlruns/artifacts/`, runs por candidato/nível, parâmetros, métricas por fold, versões Python/NumPy/pandas/scikit-learn/MLflow, seed, hash de código, commit e estado sujo do Git | O registrador apenas importa resultados existentes; não treina. Sem DVC remote compartilhado, cache e MLflow permanecem locais à máquina. |

DVC registra dependências e saídas do estágio em `dvc.lock` após a primeira reprodução. O CSV de previsões (~253 MB) permanece na pasta de resultados e é declarado `cache: false` no DVC; também está no `.gitignore`. Os demais resultados compactos podem ser versionados pelo cache local do DVC. Nenhum dataset é duplicado pela configuração.

## Comandos a partir da raiz

Instale as ferramentas opcionais apenas quando for habilitar DVC/MLflow; elas não fazem parte dos testes científicos nem foram instaladas nesta etapa:

```bash
python -m pip install -r requirements-mlops.txt
```

Com os três CSVs brutos locais e dependências de modelagem instaladas, reproduza o estágio explicitamente:

```bash
dvc repro temporal_cv
```

Isso executa a busca temporal completa. Não é necessário executar esse comando para abrir os resultados já existentes. Para registrar os resultados existentes sem treinar:

```bash
python -m experiments.temporal_cv.mlops
```

O backend usa SQLite local porque o backend de arquivos do MLflow 3 está em modo de manutenção. Para consultar o rastreamento no navegador local:

```bash
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db --host 127.0.0.1 --port 5000
```

O URI de rastreamento é local e não requer servidor ou serviço pago. O logger registra o HEAD e marca se a árvore Git estava suja; para atribuir resultados a um commit imutável, faça o registro após versionar as alterações relevantes.

### Validação local retrospectiva

Na validação local de novembro de 2026, o registrador foi executado sobre os resultados já existentes, sem treinar novamente nem repetir a busca. O SQLite local contém 43 runs: um run pai e 42 runs de candidatos; todos estão marcados com `record_type=retrospective_import`, seed 42 e commit registrado `9ccc7381e3662bba758d311047f0805083bcdd06`. O commit identifica a revisão original dos resultados importados, não esta revisão documental. A base `mlruns/mlflow.db` e os artefatos MLflow permanecem locais e ignorados pelo Git.

DVC 3.67.1 e MLflow 3.18.0 foram validados em um ambiente virtual local isolado. A configuração DVC foi verificada sem executar `dvc repro`; portanto, esta validação não demonstra uma reprodução integral do pipeline.

## Dependências, CI e limitações

`requirements-mlops.txt` declara DVC 3.x e MLflow 2.x/3.x como opcionais. As versões locais informadas acima foram instaladas manualmente no ambiente virtual MLOps; não fazem parte dos ambientes científicos nem são necessárias nos testes. O workflow científico existente instala somente `requirements-modeling.txt` e executa os testes; não depende de DVC/MLflow e não dispara treinamento. O pipeline não baixa dados. Uma reprodução em outra máquina requer fornecer os três arquivos brutos de forma autorizada e idêntica. O manifesto preservado é registrado como hash, mas os arquivos brutos não têm ponteiro DVC nem armazenamento remoto configurado nesta etapa.

O hash do commit identifica o HEAD disponível, mas não torna alterações não commitadas reprodutíveis; por isso o estado sujo e o hash do script são registrados. O benchmark original usa uma metodologia retrospectiva diferente, já inspecionada, e não é um holdout cego. As métricas complementares incluem rótulos censurados e devem ser relatadas com essa ressalva.
