# Viabilidade do dataset Olist para precificação dinâmica

**Tema 7 — Danylo e William**  
**Análise executada em 19/09/2026.** Dados reais; nenhum treinamento ou resultado preditivo nesta etapa.

## 1. Parecer executivo

**Viabilidade parcial e condicionada.** A Olist é adequada para aquisição, limpeza, análise exploratória e previsão de vendas observadas. É limitada para estimar a reação da demanda ao preço de um produto: a maioria dos produtos tem pouco histórico; não há exposição das ofertas, estoque nem preços de concorrentes externos.

Recomendação: manter Olist como base real, adotar semana como período e restringir experimentos de produto a itens recorrentes, com um modelo compartilhado entre produtos. Usar categoria-semana como análise auxiliar e alternativa para comparação de previsões. Não substituir silenciosamente a recomendação de preço de produto por uma previsão de categoria. Simulações de preços serão exploratórias, sem alegar elasticidade causal ou ganho comprovado de receita. Se for exigida validação empírica de preço ótimo ou demanda real não atendida, será necessária uma base complementar com histórico de ofertas e disponibilidade.

Persistência local CSV/JSON é suficiente nesta fase. PostgreSQL fica como melhoria futura; CI, FastAPI, Streamlit e modelos finais não foram implementados.

## 2. Fonte, aquisição e rastreabilidade

Fonte oficial: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Download público executado por `https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce`, sem autenticação. O ZIP tem **44.717.580 bytes**, foi validado e contém nove CSVs. Origem, data e hashes SHA-256 estão em `data/raw/manifest.json`; todos os arquivos foram preservados em `data/raw/`. O endpoint não fixa versão: o ZIP local e seus hashes identificam o material desta análise. Para eventual redistribuição, consultar as condições na fonte; o repositório ignora os dados brutos.

## 3. Tabelas necessárias

| Arquivo em data/raw/ | Linhas | Uso proposto |
|---|---:|---|
| olist_orders_dataset.csv | 99.441 | Essencial: identificador, instante da compra e status |
| olist_order_items_dataset.csv | 112.650 | Essencial: produto, vendedor, preço e frete por item |
| olist_products_dataset.csv | 32.951 | Essencial: categoria e atributos do produto |
| olist_sellers_dataset.csv | 3.095 | Opcional: localização do vendedor; seller_id já existe nos itens |
| olist_customers_dataset.csv | 99.441 | Opcional: cliente recorrente e localização; não necessário ao MVP |
| product_category_name_translation.csv | 71 | Opcional: tradução; manter nomes originais evita perda de categorias |
| olist_order_payments_dataset.csv | 103.886 | Fora do núcleo: parcelas e pagamentos não são preço unitário |
| olist_order_reviews_dataset.csv | 99.224 | Fora do núcleo: avaliações surgem após a compra e podem gerar vazamento |
| olist_geolocation_dataset.csv | 1.000.163 | Fora do núcleo: volume e duplicatas desnecessários nesta fase |

Junções executadas: itens → pedidos por `order_id` e itens → produtos por `product_id`, ambas muitos-para-um. Nenhum item sem correspondência. Não unir pagamentos ou reviews diretamente aos itens sem agregação: isso pode multiplicar linhas e inflar vendas.

## 4. Cobertura e qualidade

- **99.441 pedidos, 112.650 itens, 32.951 produtos vendidos, 73 categorias não nulas e 3.095 vendedores.** Cada linha de item representa uma unidade; `order_item_id` é uma sequência dentro do pedido, não uma quantidade a somar.
- Compras registradas de **04/09/2016 a 17/10/2018**. Os pedidos mais tardios não necessariamente possuem itens. A cobertura mensal de itens revela poucas observações nas extremidades.
- **96.478 pedidos entregues**, correspondendo a **110.197 itens** e **32.216 produtos**. Demais status: 1.107 enviados, 625 cancelados, 609 indisponíveis, 314 faturados, 301 em processamento, 5 criados e 2 aprovados.
- Não há preço ausente ou não positivo, frete negativo nem instante de compra ausente. Chaves de pedidos e produtos são únicas; não há repetição de `(order_id, order_item_id)`.
- **610 produtos sem categoria**. A análise os identifica como `sem_categoria`, sem inventar rótulos. A tradução não contempla `pc_gamer` e `portateis_cozinha_e_preparadores_de_alimentos`.
- Geolocalização tem **261.831 linhas integralmente duplicadas**; nenhuma das outras tabelas tem duplicatas integrais. Duplicata geográfica não equivale automaticamente a erro de transação.

Preço unitário de todos os itens, sem frete: mínimo **R$ 0,85**; quartil 25% **R$ 39,90**; mediana **R$ 74,99**; média **R$ 120,65**; quartil 75% **R$ 134,90**; percentil 95% **R$ 349,90**; máximo **R$ 6.735,00**. A amplitude entre produtos não prova variação temporal no mesmo produto. Valores extremos devem ser investigados por categoria, não removidos automaticamente.

A janela diária de diagnóstico é **01/01/2017–31/08/2018**: 608 dias, 96.211 pedidos entregues e 109.880 itens. Para semanas completas, usamos **02/01/2017–26/08/2018**: 86 semanas de segunda a domingo e 109.748 itens. Esse recorte evita as extremidades rarefeitas; não significa disponibilidade contínua de cada produto.

## 5. Variação de preço por produto

População desta seção: todos os itens de pedidos entregues, antes do recorte temporal.

| Medida | Resultado |
|---|---:|
| Produtos com venda entregue | 32.216 |
| Produtos com apenas um item vendido | 17.716 (54,99%) |
| Produtos vendidos em pelo menos dois dias distintos | 12.991 |
| Produtos com mais de um preço em centavos | 5.806 (18,02%) |
| Produtos com mudança da mediana de preço entre dias | 5.806 |
| Pares produto-vendedor | 33.659 |
| Pares produto-vendedor vendidos em pelo menos dois dias | 13.212 |
| Pares com mudança da mediana de preço entre dias | 5.360 |
| Produtos com essa variação dentro de algum mesmo vendedor | 5.192 |
| Produtos com ≥20 pedidos, ≥8 semanas com venda e ≥2 preços | 491 |

Por produto, a mediana é **1 item vendido e 1 semana com venda**; o percentil 95% é 11 itens e 8 semanas. O máximo é 520 itens e, separadamente, 75 semanas com venda. Esses máximos não necessariamente pertencem ao mesmo produto.

Método: preços arredondados para centavos; comparação de medianas por dia, primeiro por produto, depois por produto-vendedor. Isso reduz a confusão entre composição de vendedores e alteração temporal. Ainda assim, somente preços transacionados são conhecidos; nenhuma conclusão sobre preços ofertados entre vendas é possível.

Os 491 produtos são um diagnóstico usando todo o histórico, **não uma seleção válida para avaliar modelos futuros**. Repetindo os critérios somente com compras de 2017 na janela semanal, restam **149 produtos**. Eles têm **12.026 itens** ao longo das 86 semanas: 7.989 em 2017 e 4.037 em 2018; apenas **121** reaparecem em 2018. A densidade de semanas com venda desse subconjunto é **32,88%**. Portanto, mesmo a seleção recorrente exige tratar inatividade e possível retirada do catálogo como limitações.

## 6. Densidade da variável de vendas

Densidade = células com ao menos uma venda / todas as combinações de entidade e período na janela. Ausência de transação não comprova demanda zero, estoque zero ou oferta ativa.

| Granularidade | Entidades | Períodos | Células | Células com venda | Densidade | Mediana de unidades nas células com venda |
|---|---:|---:|---:|---:|---:|---:|
| Produto-dia | 32.081 | 608 | 19.505.248 | 92.317 | 0,47% | 1 |
| Produto-semana | 32.040 | 86 | 2.755.440 | 77.352 | 2,81% | 1 |
| Categoria-dia | 74 | 608 | 44.992 | 18.685 | 41,53% | 3 |
| Categoria-semana | 74 | 86 | 6.364 | 4.379 | 68,81% | 7 |

As 74 entidades de categoria incluem `sem_categoria`. As populações diária e semanal diferem por causa do recorte de semanas completas.

Como triagem descritiva, **18 categorias** têm vendas em pelo menos 90% das semanas e mediana de pelo menos 20 unidades/semana. Representam **92.944 dos 109.748 itens** semanais (84,69%). Esse filtro usa todo o intervalo apenas para diagnóstico; na modelagem deverá ser recalculado exclusivamente no treino.

Exemplos: `cama_mesa_banho`, 10.933 unidades, 86 semanas ativas, mediana de 130,5 unidades/semana; `beleza_saude`, 9.402, 86 e 85; `esporte_lazer`, 8.398, 85 e 96; `moveis_decoracao`, 8.093, 86 e 83.

**Conclusão:** produto-dia é muito esparso para a proposta inicial. Categoria-semana sustenta melhor previsão de vendas agregadas. Produto-semana em subconjunto recorrente é uma experiência viável, porém limitada; não é justificativa para um modelo individual por produto nem para operação em tempo real comprovada.

## 7. Variáveis exigidas e lacunas

| Variável | Situação na Olist | Tratamento correto |
|---|---|---|
| Preço | Preço realizado por item | Não equivale ao preço anunciado continuamente |
| Vendas | Itens e pedidos observados | Contar linhas de item e pedidos únicos separadamente |
| Estoque | Ausente | Futuro parâmetro de cenário informado pelo usuário; sem reconstrução fictícia |
| Demanda | Demanda latente ausente | Usar vendas observadas como proxy e declarar limitação |
| Horário | Instante da compra disponível | Derivar calendário; o MVP semanal não justifica previsão horária |
| Categoria | Disponível, com ausências | Preservar categoria original e sinalizar ausências |
| Concorrência | Preços de concorrentes externos e ofertas ausentes | Não chamar outros vendedores ou média de categoria de concorrência real |
| Histórico de compras | Disponível por pedido, produto e cliente | Usar somente histórico anterior ao instante de previsão |
| Custo e margem | Ausentes | Não prometer otimização de lucro; cenários de receita apenas |
| Exposição, visitas e disponibilidade de catálogo | Ausentes | Não estimar conversão nem interpretar toda ausência de venda como rejeição ao preço |

## 8. Proposta de dataset de modelagem

**Núcleo proposto:** uma linha por produto-semana, produtos selecionados somente no treino, regressão compartilhada entre produtos para prever unidades na semana seguinte. Identificadores não serão usados como números contínuos. O índice semanal representa vendas registradas, não exposição de ofertas. Preços inexistentes permanecem ausentes, acompanhados de sinalizador e idade; não usar preenchimento com valores futuros.

| Campo | Descrição | Origem / disponibilidade |
|---|---|---|
| product_id | Chave do produto; identificador | Itens e produtos |
| week_start | Segunda-feira da semana a prever | Calendário, conhecido previamente |
| category | Categoria, com marcador de ausência | Produtos; atributo tratado como estático por hipótese documentada |
| units_lag_1 | Unidades da semana anterior | Contagem de itens, deslocada uma semana |
| units_lag_2 | Unidades de duas semanas antes | Histórico de itens |
| units_lag_4 | Unidades de quatro semanas antes | Histórico de itens |
| units_mean_4w | Média das quatro semanas anteriores | Janela encerrada antes da semana-alvo |
| units_std_4w | Variação das vendas nas quatro semanas anteriores | Mesmo histórico deslocado |
| active_weeks_8w | Semanas com transação nas oito anteriores | Itens; não representa disponibilidade |
| weeks_since_last_sale | Tempo desde a última venda registrada | Datas anteriores ao alvo |
| last_observed_price | Mediana de preço da última semana com transação anterior | Preço de itens; proxy histórica, não preço atual garantido |
| price_age_weeks | Idade do preço acima | Datas de transações anteriores |
| price_missing | Indica falta de preço histórico | Derivação; imputação ajustada só no treino |
| price_change_last_observed | Mudança entre as duas últimas semanas com preços observados | Histórico de preços anterior ao alvo |
| freight_median_lag | Mediana histórica recente de frete por item | Itens, somente semanas anteriores |
| sellers_count_4w | Vendedores com venda nas quatro semanas anteriores | seller_id; não concorrentes ofertando atualmente |
| category_units_lag_1 | Vendas da categoria na semana anterior | Categoria + itens + datas |
| category_units_mean_4w | Média recente de vendas da categoria | Histórico deslocado |
| week_of_year_sin / cos | Duas features cíclicas de semana do ano | Calendário conhecido |
| time_index | Número de semanas desde o início do recorte | Calendário; ajuda a representar tendência |
| target_units | Alvo: unidades registradas na semana-alvo | Contagem futura para supervisão; nunca entrada |

Essas features são uma **proposta**, ainda não uma matriz final gerada. Usar preços defasados permite avaliar previsão histórica honestamente, mas **não identifica o efeito de intervir no preço**. Substituir `last_observed_price` por um preço candidato na aplicação seria uma hipótese de simulação, que precisará aparecer explicitamente na documentação e nos resultados. Para uma modelagem direta de resposta ao preço, falta observar o preço ofertado antes e durante a semana-alvo, inclusive sem vendas.

Dataset auxiliar: categoria-semana, com as mesmas famílias de defasagens, calendário e agregações adequadas. Já foi salvo `data/processed/category_week_diagnostic.csv`, com 6.364 linhas e contagens/estatísticas contemporâneas para diagnóstico. **Não alimentar o modelo diretamente com preço médio, número de produtos ou pedidos da própria semana-alvo:** isso traz informação futura. A mudança do preço agregado também pode ser simples mudança no mix de produtos.

Parâmetros futuros do simulador — `current_price`, `available_stock`, `candidate_price`, limites de reajuste e demanda informada — não são features históricas observadas nesta base. Devem ficar em um contrato de cenário separado, com origem explícita. Não há necessidade de fabricar colunas de estoque ou concorrência.

## 9. Plano objetivo para continuar

1. Fixar produto-semana como experimento principal restrito e categoria-semana como análise auxiliar. Confirmar que a entrega será um protótipo de simulação com limitações empíricas declaradas.
2. Preparar o painel com defasagens e ausência de preço explícita. Definir como distinguir ausência de registro de zero de vendas observado; nunca chamar essa decisão de estoque conhecido.
3. Separar treino em 2017, validação entre janeiro e abril de 2018 e teste entre maio e agosto de 2018, preservando semanas completas. Selecionar produtos/categorias e ajustar transformações somente no treino. Confirmar quantidade de exemplos após janelas e filtros antes de consolidar esse corte.
4. Comparar previsão simples de referência (última semana e média móvel) com regressão linear, polinomial, Random Forest e Gradient Boosting. Avaliar MAE, RMSE e R², com erros por produto/categoria, avaliação temporal e limites dos dados. Nenhum desempenho foi medido ainda.
5. Documentar que o uso de status final `delivered` nesta auditoria seleciona retrospectivamente vendas concluídas. Em backtest operacional, somente transações disponíveis até cada corte poderão compor features: não usar conhecimento futuro de entrega. Reavaliar o alvo como pedidos realizados ou adotar atraso de maturação explícito. O status atual de pedidos cancelados não informa quando ocorreu o cancelamento.
6. Só depois implementar cenários de preço, com limites e estoque informado, fallback para histórico insuficiente e comparação com preço mantido. Ganho previsto pelo mesmo modelo que escolhe o preço é uma simulação interna, não validação independente de ganho real.
7. Se a previsão não superar referências simples, ou a avaliação exigir efeito real de preço/estoque/concorrência, complementar a base antes de desenvolver a interface. Aprendizado por reforço não resolve essas lacunas.

## 10. Evidências e reprodução

Ambiente utilizado: Python 3.12.14, pandas 2.2.3 e NumPy 2.3.5. Dependências em `requirements-analysis.txt`. Executar a partir da raiz:

```bash
python scripts/download_olist.py
python scripts/validate_olist.py
```

O primeiro comando valida ZIP e hashes; o segundo executa junções verificadas, auditoria de colunas, variação temporal e densidade. Resultados regeneráveis:

- `reports/metricas.json`: totais e distribuições;
- `reports/inventario.csv` e `reports/qualidade_colunas.csv`: arquivos, duplicatas e ausências;
- `reports/cobertura_mensal.csv`: meses com itens observados;
- `reports/produtos.csv` e `reports/variacao_produto_vendedor.csv`: recorrência e variação;
- `reports/densidade.csv` e `reports/categorias.csv`: densidade e triagem de categorias;
- `reports/produtos_elegiveis_treino.csv` e `reports/subconjunto_produtos.json`: seleção restrita a 2017;
- `data/processed/category_week_diagnostic.csv`: painel descritivo de categorias.

Este relatório interpreta os arquivos acima; ele não é reescrito automaticamente pelo script. Não foram criados modelos finais, métricas de previsão, dados sintéticos, API ou dashboard.
