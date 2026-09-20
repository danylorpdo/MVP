# Conteúdo da apresentação: Motor de Precificação Dinâmica para Marketplace

**Dupla:** Danylo e William  
**Disciplina:** Mineração de Dados em Engenharia de Software  
**Tema 7**  
**Entrega:** proposta de 10 slides, incluindo abertura e demonstração. Este documento especifica conteúdo e recursos visuais. Não contém slides produzidos.  
**Duração sugerida:** 15 minutos, incluindo cerca de 3 minutos de demonstração. A divisão de falas é uma sugestão.  
**Referência:** estado validado do MVP em 20/09/2026.

## Resumo executivo para orientar a apresentação

O projeto usa o Brazilian E-Commerce Public Dataset by Olist para estudar previsão de vendas semanais e demonstrar cenários de precificação. A base contém 99.441 pedidos e 112.650 itens. A baixa recorrência dos produtos motivou um experimento principal com 136 produtos selecionados exclusivamente a partir do treino. Entre seis métodos, MovingAverage4 apresentou o menor MAE na validação com rótulo disponível e permaneceu como campeão de previsão.

Um experimento independente identificou associação histórica negativa entre preço e quantidade, com elasticidade log-log compartilhada de aproximadamente −1,526. O MVP combina demanda-base, esse fator experimental e estoque informado para comparar a receita estimada de candidatos dentro de ±10% do preço atual. A aplicação reúne Streamlit, FastAPI e SQLite, com 52 testes distintos aprovados na finalização. O resultado é uma demonstração acadêmica reproduzível de cenários, sem comprovação de efeito causal ou ganho real de receita.

## Estrutura e distribuição sugerida

| Slide | Título | Tempo | Apresentador sugerido |
|---|---|---:|---|
| 1 | Motor de Precificação Dinâmica para Marketplace | 0:45 | Danylo |
| 2 | Dados Olist e recorte do experimento | 1:15 | Danylo |
| 3 | Aplicação do CRISP-DM | 1:00 | Danylo |
| 4 | Preparação temporal e prevenção de vazamento | 1:15 | Danylo |
| 5 | Comparação dos modelos e escolha do MovingAverage4 | 1:45 | Danylo |
| 6 | Experimento independente de resposta ao preço | 1:45 | William |
| 7 | Funcionamento do motor híbrido | 1:15 | William |
| 8 | Arquitetura de software e API | 1:15 | William |
| 9 | Limitações e evidências de validação | 1:00 | William |
| 10 | Demonstração do MVP | 3:00 | Ambos |

Total sugerido: 14min15s, com 45s de margem para transições. As notas de fala e os anexos abaixo não são slides adicionais.

---

## Slide 1 — Motor de Precificação Dinâmica para Marketplace

**Objetivo:** apresentar o problema, a entrega e o caráter experimental.

### Conteúdo exato na tela

**Título:** Motor de Precificação Dinâmica para Marketplace  
**Subtítulo:** Simulação acadêmica de cenários semanais com dados da Olist  
**Autoria:** Danylo e William · Tema 7

- Objetivo: comparar cenários de receita a partir de preço, demanda-base e estoque informado.
- Entrega: aplicação com interface, API e histórico de simulações.

**Frase de destaque:** “Previsão de vendas e associação histórica ao preço sustentam uma demonstração de cenários.”

### Visual

Abertura apenas com título, autoria e texto acima. Não usar print de código, imagem genérica de comércio ou gráfico neste slide.

### Fala sugerida

“Estudamos como transformar dados históricos de comércio eletrônico em uma aplicação que compara cenários semanais. Primeiro avaliamos previsão de vendas. Depois investigamos associação entre preço e quantidade. O sistema permite explorar essas hipóteses e mantém suas limitações visíveis.”

**Fontes:** F1, F2, F3 e F4, identificadas no catálogo ao final.

---

## Slide 2 — Dados Olist e recorte do experimento

**Objetivo:** mostrar dimensão, qualidade e motivo do recorte.

### Conteúdo exato na tela

**Título:** Dados Olist e recorte do experimento

| Base original | Quantidade |
|---|---:|
| Arquivos CSV | 9 |
| Pedidos | 99.441 |
| Itens de pedidos | 112.650 |
| Produtos no catálogo | 32.951 |
| Categorias não nulas | 73 |
| Vendedores | 3.095 |

Ao lado da tabela, apresentar três linhas:

- Produto-semana: apenas **2,81%** das combinações têm vendas no diagnóstico amplo.
- Experimento principal: **136 produtos recorrentes**, selecionados no treino.
- Categoria-semana: análise auxiliar com **14 categorias** selecionadas no treino.

**Rodapé:** “610 produtos sem categoria. Junções verificadas: nenhum item sem pedido ou produto correspondente.”

### Visual

Usar a tabela acima e um gráfico simples de duas barras a ser montado na futura apresentação a partir de F6: **produto-semana 2,81%** e **categoria-semana 68,81%**. Eixo: “Combinações com ao menos uma venda (%)”, de 0 a 100. Legenda: “Diagnóstico amplo, 86 semanas de 02/01/2017 a 26/08/2018”. Não gerar o gráfico nesta etapa.

Essas densidades pertencem ao universo amplo do diagnóstico, não ao subconjunto de 136 produtos ou às 14 categorias do experimento. Não usar as 18 categorias da triagem retrospectiva como quantidade final da modelagem.

### Fala sugerida

“A base é grande, mas o histórico de cada produto é esparso. Por isso, o tamanho total não garante uma boa previsão individual. Restringimos o experimento a produtos recorrentes e mantivemos categoria-semana como análise auxiliar. Uma linha de item representa uma unidade. A base não informa estoque nem demanda não atendida.”

**Fontes:** F1, F5, F6, F8 e F9.

---

## Slide 3 — Aplicação do CRISP-DM

**Objetivo:** relacionar cada fase a uma entrega concreta.

### Conteúdo exato na tela

**Título:** Aplicação do CRISP-DM

| Fase | Aplicação no projeto |
|---|---|
| Entendimento do negócio | Comparar cenários semanais de receita para marketplace |
| Entendimento dos dados | Aquisição Olist, qualidade, recorrência e lacunas de informação |
| Preparação | Junções verificadas, painel semanal, defasagens e cortes temporais |
| Modelagem | Seis métodos de previsão e experimento independente de resposta ao preço |
| Avaliação | MAE, RMSE, R², análise de extrapolação e seleção pela validação |
| Implantação | Motor Python, FastAPI, Streamlit, SQLite, testes e documentação |

**Rodapé:** “As limitações dos dados orientaram o recorte e o alcance da aplicação.”

### Visual

Representar as seis fases em sequência numerada na futura apresentação, usando exatamente os textos da tabela. Indicar que a avaliação realimentou o entendimento do problema. Não acrescentar ícones decorativos ou capturas de tela. O fluxo é uma especificação textual neste documento.

### Fala sugerida

“Seguimos o CRISP-DM vinculando cada fase a uma entrega verificável. A investigação dos dados limitou a proposta a cenários exploratórios. A etapa de implantação disponibiliza essa análise em software local, sem treinamento durante uma simulação.”

**Fontes:** F1 a F4. O mapeamento das seis fases é uma síntese editorial das entregas existentes.

---

## Slide 4 — Preparação temporal e prevenção de vazamento

**Objetivo:** explicar como a avaliação respeitou o tempo.

### Conteúdo exato na tela

**Título:** Preparação temporal e prevenção de vazamento

**Linha do tempo:**

| Treino | Validação | Teste |
|---|---|---|
| 2017 | Janeiro–abril/2018 | Maio–agosto/2018 |
| 6.528 linhas | 2.312 linhas | 2.176 linhas |

**Regras:**

- Seleção de produtos e ajuste de transformações somente no treino.
- Histórico usa compras e entregas confirmadas antes da semana prevista.
- Quatro semanas iniciais de aquecimento e exclusão da semana de 30/04–06/05/2018.
- Alvo: itens de pedidos entregues, agrupados pela semana da compra.

**Destaque:** “Rótulo disponível na data de corte e alvo eventual são avaliações diferentes.”

### Visual

Usar a linha do tempo acima como visual central. Sob ela, escrever “Compra e confirmação de entrega anteriores à previsão”. Não usar screenshot de CSV ou código.

### Fala sugerida

“O status final de entrega poderia revelar o futuro. Por isso, as variáveis históricas só usam entregas já conhecidas no instante de previsão. O treino usa confirmações anteriores a janeiro de 2018, e a seleção usa as conhecidas antes de maio. Isso evita vazamento, mas deixa rótulos incompletos perto dos cortes. O teste avalia o alvo eventual, sem participar da escolha do campeão.”

**Notas de apoio:** 48 semanas de treino, 17 de validação e 16 de teste após os recortes. A avaliação incorpora histórico disponível a cada nova semana, com os parâmetros congelados. As semanas sem registro de venda não comprovam ausência de demanda ou disponibilidade de estoque.

**Fontes:** F2 e F8.

---

## Slide 5 — Comparação dos modelos e escolha do MovingAverage4

**Objetivo:** justificar a escolha pela regra definida, sem escolher um vencedor pelo teste.

### Conteúdo exato na tela

**Título:** Comparação dos modelos e escolha do MovingAverage4

| Modelo | MAE de seleção |
|---|---:|
| **MovingAverage4** | **0,8007** |
| Polinomial | 0,9213 |
| PreviousWeek | 0,9239 |
| Random Forest | 0,9367 |
| Regressão Linear | 0,9557 |
| Gradient Boosting | 0,9944 |

**Legenda da tabela:** “Produto-semana. Validação com rótulo disponível em 01/05/2018. MAE em unidades por produto-semana. Menor é melhor.”

**Conclusão visível:** “MovingAverage4 venceu pelo menor MAE de validação. Sua regra usa a média das quatro semanas anteriores disponíveis.”

**Nota crítica visível:** “Polinomial: todas as 2.176 previsões de teste eram negativas antes do truncamento para zero.”

### Visual

Usar G1, o gráfico existente `product_mae.png`, ao lado da tabela, mantendo título, eixos e legenda. Acrescentar abaixo dele:

> “Gráfico: avaliação com alvo eventual. A tabela mostra o critério efetivamente usado na seleção.”

O gráfico tem teste em azul e validação em laranja. Não relabelar o MAE 0,8760 do gráfico como 0,8007. Se a montagem futura exigir mais espaço, manter a tabela como elemento principal e levar G1 para as notas de apoio, sem reduzir a legibilidade. Não regenerar ou sobrescrever a imagem original.

### Fala sugerida

“Comparamos duas referências simples e quatro regressões. MovingAverage4 obteve o menor MAE de seleção, aproximadamente 13,33% abaixo de PreviousWeek nessa validação. A simplicidade ajuda a explicar e reproduzir o resultado, mas a escolha veio da métrica. A polinomial ficou em segundo no ranking, porém falhou na extrapolação: o truncamento para zero favorece seu MAE em um conjunto com muitas semanas sem vendas.”

**Apoio para perguntas:** no teste eventual, MovingAverage4 teve MAE **0,5381**, RMSE **1,9778** e R² **0,0169**. PreviousWeek teve MAE **0,5207**, e Random Forest teve RMSE **1,8749**. Portanto, não afirmar que MovingAverage4 venceu todas as métricas ou todos os períodos. O conjunto de teste tem **81,43%** de linhas com alvo zero. O modelo Linear venceu no experimento auxiliar de categorias, sem substituir o campeão do produto-semana.

**Fontes:** F2, F7, F8 e F9. A redução de 13,33% deriva dos MAEs não arredondados de MovingAverage4 e PreviousWeek em F7.

---

## Slide 6 — Experimento independente de resposta ao preço

**Objetivo:** separar previsão de vendas da hipótese de sensibilidade ao preço.

### Conteúdo exato na tela

**Título:** Experimento independente de resposta ao preço

| Modelo | MAE de validação disponível |
|---|---:|
| Log-log compartilhado | 1,7518 |
| Random Forest | 1,7528 |
| Gradient Boosting | 1,7901 |
| Log-log por categoria | 1,8689 |
| Regressão Linear | 2,3616 |
| Polinomial regularizada | 2,8774 |

**Legenda:** “735 observações de produto-semana com transações e informação disponível no corte. População diferente do experimento de demanda.”

**Destaques:**

- Elasticidade compartilhada: **−1,526**.
- Suporte individual mínimo: **35 de 136 produtos**.
- Log-log compartilhado: candidato experimental com vantagem mínima sobre Random Forest.

**Aviso visível:** “Associação histórica observacional. A aplicação do fator à demanda-base é uma hipótese não validada.”

### Visual

Usar G3, `sensitivity_examples.png`. Para caber ao lado da tabela, usar somente o painel superior esquerdo, identificado por **99a4788c / 2018-05-07**, preservando a legenda de todos os modelos, os eixos e o título do painel. Legenda editorial: “Exemplo diagnóstico de sensibilidade com histórico fixo. Recorte de um dos seis casos do relatório.” A imagem original deve permanecer intacta. O recorte serve à legibilidade e não representa todos os produtos.

### Fala sugerida

“Este experimento usa semanas com transações, por isso seus erros não são diretamente comparáveis aos do painel completo. O log-log compartilhado apresentou associação negativa interpretável e o menor MAE entre os candidatos com preço, por uma diferença muito pequena. Utilizamos apenas seu fator relativo como hipótese de simulação. Não estimamos uma curva confiável para cada produto, e o fallback por categoria não resolveu a limitação.”

**Apoio para perguntas:** intervalo bootstrap de 95% do coeficiente: **[−2,130; −1,094]**, que não elimina confundimento. No teste, o log-log compartilhado apresentou MAE **2,0292** e R² **−0,0130**. Na ablação, Random Forest sem os campos de cenário de preço teve MAE de validação disponível **1,7505**, levemente menor que o log-log com preço. Logo, não afirmar que incluir preço comprovadamente melhora a previsão.

**Fontes:** F3, F10, F11 e F12.

---

## Slide 7 — Funcionamento do motor híbrido

**Objetivo:** explicar o cálculo de um cenário e a comparação de candidatos.

### Conteúdo exato na tela

**Título:** Funcionamento do motor híbrido

1. **Demanda-base:** MovingAverage4 histórico ou valor semanal informado.
2. **Resposta experimental:** fator = (preço candidato / preço atual)^−1,525585.
3. **Demanda ajustada:** demanda-base × fator.
4. **Limite de estoque:** unidades vendáveis = mínimo(demanda ajustada, estoque informado).
5. **Receita estimada:** preço candidato × unidades vendáveis.
6. **Comparação:** selecionar o candidato de maior receita estimada na grade.

**Faixa e regras:** “Grade padrão: −10%, −5%, 0%, +5%, +10%. Preço atual incluído. Empates preferem a menor alteração.”

**Rodapé:** “Receita estimada depende das hipóteses. O sistema sinaliza extrapolação e suporte insuficiente.”

### Visual

Na futura montagem, apresentar os seis passos como fluxo numerado. Exibir uma única ramificação na entrada: “MovingAverage4 histórico” / “demanda manual”. A sequência se reúne antes do fator de preço. Não usar uma curva como se tivesse sido validada causalmente.

### Fala sugerida

“O modelo de demanda fornece a base semanal. O preço candidato modifica essa base por um fator experimental. O estoque informado limita as unidades vendáveis. Calculamos a receita de cada candidato e comparamos com manter o preço atual. Com demanda ou estoque zero, o empate preserva o preço atual.”

**Nota técnica:** o aplicativo usa o coeficiente completo **−1,5255852107075418** do artefato. A abreviação no slide é apenas visual. Quantidades fracionárias representam expectativas. O motor arredonda preços e receita para centavos e respeita os limites configurados. A elasticidade individual presente no estudo não entra no motor.

**Fontes:** F4 e F13.

---

## Slide 8 — Arquitetura de software e API

**Objetivo:** mostrar a arquitetura final e como a pesquisa chega à interface.

### Conteúdo exato na tela

**Título:** Arquitetura de software e API

**Arquitetura:**

| Componente | Responsabilidade |
|---|---|
| Streamlit | Formulário, indicadores, gráficos e histórico |
| FastAPI + schemas Pydantic | Contratos HTTP e validação de entrada |
| Motor Python | Cálculo e comparação dos cenários |
| Catálogo de artefatos | Histórico, coeficiente e hashes dos arquivos congelados |
| SQLite | Armazenamento da entrada e do resultado de cada simulação |

**Rotas principais:**

```text
GET  /health
GET  /api/v1/products
GET  /api/v1/products/{id}/history
GET  /api/v1/metadata
POST /api/v1/simulations
GET  /api/v1/simulations
GET  /api/v1/simulations/{id}
```

**Rodapé:** “Documentação interativa em /docs. A aplicação consulta artefatos locais e não treina durante a simulação.”

### Visual

Na futura montagem, usar o seguinte esquema de conexões em lugar de fotografias ou logos decorativos:

- Navegador abre a interface Streamlit.
- O processo Streamlit faz chamadas HTTP à FastAPI.
- A FastAPI valida a entrada e chama o motor com o catálogo de artefatos.
- O catálogo lê os quatro arquivos congelados do aplicativo.
- A FastAPI salva entrada e resultado no SQLite.
- O resultado retorna em JSON à interface, que apresenta os cenários.

Reservar o lado esquerdo para o esquema e o direito para as rotas. A tabela de responsabilidades orienta os rótulos do esquema e não precisa ser repetida na tela. Os scripts científicos ficam identificados como “preparação e pesquisa offline”, separados da execução de uma simulação.

**Print de apoio:** P4, documentação Swagger com `POST /api/v1/simulations` expandido. Usar durante a demonstração ou nas notas, sem ocupar o espaço do esquema com um print ilegível.

### Fala sugerida

“A interface conversa com a API por HTTP. A API valida os dados, executa o motor e persiste o resultado. Cada simulação registra versões e hashes dos artefatos. O SQLite mantém o histórico após reiniciar a API. Docker e Compose estão preparados, mas a execução em contêineres ainda não foi validada na máquina de finalização.”

**Fontes:** F4, F14 e F15.

---

## Slide 9 — Limitações e evidências de validação

**Objetivo:** apresentar o alcance do resultado e a qualidade do software.

### Conteúdo exato na tela

**Título:** Limitações e evidências de validação

**Limitações dos dados e do cenário:**

- Ausência de estoque histórico, concorrência, custos e demanda não atendida.
- Preço realizado em transações não equivale a preço ofertado continuamente.
- Pouco suporte individual, rótulos censurados e mudança temporal.
- Associação observacional sem demonstração de efeito causal ou ganho real.

**Evidências do MVP:**

- **52 testes distintos aprovados:** 41 do aplicativo e 11 científicos.
- Integração Streamlit–API–motor e persistência após reinício testadas.
- Instalação limpa validada e 100 arquivos científicos preservados por hash.

**Rodapé:** “Docker pendente de execução. Conferência visual no navegador da apresentação ainda necessária.”

### Visual

Usar dois blocos de texto com os títulos acima, sem transformar todas as linhas em cartões. O número **52** pode receber destaque tipográfico. Evidência de apoio: log L1 e relatório F4. Um print de testes, se usado como reserva, deve mostrar o resumo de cada suíte e não apresentar a repetição em ambiente limpo como testes novos.

### Fala sugerida

“A validação de software confirma o comportamento implementado. Ela não comprova a hipótese econômica. O sistema mantém os alertas e mostra quando extrapola a faixa histórica. Nosso resultado permite uma demonstração acadêmica reproduzível, com limitações explícitas.”

**Apoio para perguntas:** no diagnóstico de sensibilidade, **56,19%** dos pontos da grade do teste ficaram fora da faixa individual de preços do treino. Esse número pertence ao experimento de resposta ao preço e não significa que 56,19% das simulações futuras necessariamente extrapolem. Permanecer dentro da faixa histórica também não garante validade causal.

**Fontes:** F1, F2, F3, F4 e L1.

---

## Slide 10 — Demonstração do MVP

**Objetivo:** mostrar uma simulação reproduzível e o efeito da restrição de estoque.

### Conteúdo exato na tela

**Título:** Demonstração do MVP

**Entradas comuns:** preço atual **R$ 100,00**, demanda manual **10 unidades/semana**, grade **±10%** com passo **5%**.

| Cenário | Estoque informado | Preço recomendado no cenário | Receita mantendo R$ 100 | Receita no candidato recomendado |
|---|---:|---:|---:|---:|
| A | 100 | R$ 90,00 | R$ 1.000,00 | R$ 1.056,94 |
| B | 2 | R$ 110,00 | R$ 200,00 | R$ 220,00 |

**Sequência curta na tela:** “Simular A e B · Consultar MovingAverage4 histórico · Reabrir resultado salvo”

**Legenda obrigatória:** “Valores calculados sob a hipótese experimental. Estoques e demanda manual são entradas de demonstração.”

### Visual

Usar P1 e P2 como prints de reserva, com indicadores e identificação do cenário. Durante a apresentação, alternar para a aplicação real. P3 demonstra os gráficos e a tabela. Não sobrepor prints densos à tabela acima. Os prints devem mostrar resultados reais da aplicação e ainda precisam ser capturados.

### Roteiro de fala e ações (cerca de 3 minutos)

| Tempo | Ação exata | O que mostrar / dizer |
|---|---|---|
| 0:00–0:20 | Abrir `http://127.0.0.1:8501`, página **Simular** | “Escolhemos um produto do catálogo e informamos um cenário semanal.” |
| 0:20–0:50 | Selecionar o produto abaixo, modo **Informar demanda semanal**, preço 100, estoque 100, demanda 10, limites 10/10, passo 5. Clicar **Comparar preços** | Mostrar R$ 90,00 e receitas R$ 1.000,00 / R$ 1.056,94. “A grade compara também manter o preço.” |
| 0:50–1:20 | Alterar somente estoque para 2 e clicar novamente | Mostrar R$ 110,00 e receitas R$ 200,00 / R$ 220,00. “Com o estoque limitando as unidades, o resultado da mesma hipótese muda.” |
| 1:20–1:45 | Descer até os dois gráficos e a tabela | Mostrar a limitação de unidades vendáveis e a linha do candidato recomendado. Ler ao menos um aviso. |
| 1:45–2:15 | Selecionar **MovingAverage4 histórico** e uma semana disponível. Confirmar preço/estoque exibidos e clicar **Comparar preços** | “A demanda-base agora vem de um recorte histórico. A data é antiga e não representa uma previsão para hoje.” Não prometer o mesmo resultado dos cenários manuais. |
| 2:15–2:40 | Abrir **Histórico** e escolher uma simulação recém-criada | Conferir ID, dados e resultado. Abrir **Rastreabilidade e versões**. |
| 2:40–3:00 | Mostrar **Metodologia** e retornar ao encerramento | “O projeto integra pesquisa e software com hipóteses e limitações documentadas.” |

**Produto fixo sugerido para A e B:** `8c591ab0ca519558779df02023177f44`, categoria **ferramentas_jardim**. A interface exibe o prefixo `8c591ab0ca51`. Faixa de preço observada no treino: **R$ 89,00 a R$ 120,00**. A grade R$ 90–110 fica dentro dessa faixa. O produto passa a triagem mínima de suporte, mas usa o mesmo coeficiente compartilhado do motor e continua sem validação causal individual. Essa escolha organiza a demonstração, não muda a seleção científica.

**Se houver tempo adicional:** mostrar P4 ao vivo em `http://127.0.0.1:8000/docs` e os campos da resposta de `POST /api/v1/simulations`. Não é necessário executar outra simulação na API durante os três minutos.

**Encerramento exato sugerido:** “Entregamos um pipeline de mineração de dados com avaliação temporal e uma aplicação de cenários rastreáveis. MovingAverage4 sustenta a demanda-base, e a resposta ao preço permanece uma hipótese experimental.”

**Fontes:** F4, F12, F13 e F16. Os valores A/B são cálculos determinísticos com os parâmetros especificados, não receita observada em uma intervenção.

---

## Inventário de gráficos e prints

### Gráficos existentes

| ID | Arquivo absoluto | Uso proposto |
|---|---|---|
| G1 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/figures/product_mae.png` | Slide 5, comparação eventual. Preservar legenda validação/teste e distinguir do critério de seleção. |
| G2 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/figures/product_weekly.png` | Reserva nas notas: totais semanais do campeão. Não interpretar ajuste agregado como precisão de cada produto. |
| G3 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response/figures/sensitivity_examples.png` | Slide 6, painel superior esquerdo com legenda. Curvas diagnósticas observacionais. |
| G4 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response/figures/response_factors.png` | Reserva para perguntas sobre sensibilidade. O relatório informa que outliers ficam ocultos somente nessa visualização. |
| G5 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/figures/category_mae.png` | Reserva caso perguntem pelo experimento auxiliar. Não misturar a escala de categoria com produto. |

G1 e G3 tiveram seu conteúdo visual inspecionado para esta proposta. Os demais são recursos de reserva referenciados nos relatórios. Nenhuma imagem foi gerada ou modificada nesta etapa.

### Prints a capturar depois, na preparação visual

Os nomes abaixo são **destinos propostos**, não arquivos já existentes. A captura não faz parte desta entrega de conteúdo.

| ID | Tela e recorte exatos | Destino proposto | Uso |
|---|---|---|---|
| P1 | Resultado do cenário A com produto, preço recomendado, as duas receitas e indicadores de demanda/estoque | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/01_cenario_A.png` | Reserva do slide 10 |
| P2 | Mesmo recorte do cenário B, após estoque 2 e nova simulação | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/02_cenario_B.png` | Comparação no slide 10 |
| P3 | Cenário B: seção **Preço, demanda e receita** e tabela dos cinco candidatos. Preservar eixos/legendas | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/03_graficos_cenarios.png` | Reserva da demonstração |
| P4 | Swagger `/docs`, `POST /api/v1/simulations` expandido, com exemplo de entrada e resposta | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/04_api_swagger.png` | Apoio ao slide 8 |
| P5 | Página **Histórico**, com o ID selecionado e início do resultado correspondente | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/05_historico.png` | Reserva da demonstração |
| P6 | Modo **MovingAverage4 histórico**, semana selecionada e mensagem de demanda disponível | `/home/danylo-oliveira/Documentos/PROJAPA/docs/prints/06_demanda_historica.png` | Reserva da demonstração |

Antes da captura, executar os cenários exatamente como descritos, manter os avisos em pelo menos uma imagem complementar e conferir que o resultado corresponde ao último envio do formulário. A interface mantém o último resultado salvo quando o usuário apenas edita campos. Evitar prints de uma página ainda carregando e não ocultar avisos para sugerir maior confiabilidade.

## Apoio numérico para a demonstração

Esta tabela serve à conferência dos prints e à resposta a perguntas. Não é um slide extra.

| Preço candidato | Demanda ajustada (aprox.) | Receita com estoque 100 | Receita com estoque 2 |
|---:|---:|---:|---:|
| R$ 90,00 | 11,7438 | R$ 1.056,94 | R$ 180,00 |
| R$ 95,00 | 10,8140 | R$ 1.027,33 | R$ 190,00 |
| R$ 100,00 | 10,0000 | R$ 1.000,00 | R$ 200,00 |
| R$ 105,00 | 9,2827 | R$ 974,68 | R$ 210,00 |
| R$ 110,00 | 8,6467 | R$ 951,14 | R$ 220,00 |

Receitas calculadas antes de arredondar a demanda exibida. Não usar números arredondados da tabela como entradas para tentar reproduzir os centavos. No cenário A, a variação relativa da receita usa a receita arredondada em centavos e é aproximadamente 5,694%. No B, é 10%. Ambos são resultados internos da simulação, sem ganho real comprovado.

## Preparação da demonstração

1. Usar a execução local Python validada. Conferir a interface no navegador que será usado na aula.
2. Verificar API em `http://127.0.0.1:8000/health` e interface em `http://127.0.0.1:8501`.
3. Ensaiar A/B, modo histórico e consulta de histórico. As simulações ficam salvas, então identificar os IDs do ensaio.
4. Capturar P1–P6 na futura etapa visual como plano de reserva, sem alterar o aplicativo.
5. Se houver falha durante a aula, usar os prints reais preparados e explicar que são registros de uma execução anterior. Não apresentar uma captura estática como execução ao vivo.
6. Não depender de Docker enquanto o ciclo de contêineres não estiver validado. Não reexecutar treinamento para apresentar o MVP.

## Perguntas prováveis e respostas curtas

**Por que usar um baseline se a disciplina pede algoritmos?**  
Comparamos os quatro algoritmos com duas referências sob a mesma política temporal. O baseline venceu o critério de seleção. Mantê-lo é uma decisão sustentada pela avaliação.

**Por que não trocar por PreviousWeek, que tem menor MAE no teste?**  
O teste mede generalização após a escolha. Usá-lo para selecionar outro campeão comprometeria a independência dessa avaliação.

**O sistema encontrou o preço ótimo?**  
Encontrou o candidato de maior receita estimada em uma grade limitada, dadas as hipóteses e entradas. A pesquisa não comprova um ótimo econômico real.

**Elasticidade negativa prova que baixar preço aumenta vendas?**  
Não. Ela resume associação histórica condicionada a semanas com transações. Promoções, exposição, disponibilidade e outros fatores não observados podem explicar parte da relação.

**O estoque vem da Olist?**  
Não. É uma entrada explícita do cenário. A Olist não fornece estoque histórico.

**Por que não usar uma elasticidade por produto?**  
Somente 35 produtos passaram a triagem mínima, que por si só não garante confiabilidade. O MVP usa um fator compartilhado experimental e informa as limitações.

**O que significam os 52 testes?**  
São 41 testes do aplicativo e 11 científicos, incluindo prevenção de vazamento, preservação dos artefatos, integração e persistência. Repetir os 41 em ambiente vazio valida a reprodução, sem aumentar a contagem de testes distintos.

## Fontes locais e rastreabilidade

Os identificadores F/G/L são referências editoriais deste roteiro. Nos slides futuros, mostrar uma fonte curta no rodapé e manter o caminho completo nas notas.

| ID | Fonte absoluta | Informação principal |
|---|---|---|
| F1 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/viabilidade_dataset.md` | Fonte Olist, qualidade, densidade e lacunas |
| F2 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/modelagem.md` | Preparação, cortes, métricas e diagnóstico polinomial |
| F3 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response.md` | Experimento separado, suporte, sensibilidade e limitações |
| F4 | `/home/danylo-oliveira/Documentos/PROJAPA/docs/validacao_mvp.md` | Estado final do software, testes e pendências |
| F5 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/metricas.json` | Números da base e qualidade |
| F6 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/densidade.csv` | Densidades no diagnóstico amplo |
| F7 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/model_metrics.csv` | MAE, RMSE e R² com identificação de alvo e partição |
| F8 | `/home/danylo-oliveira/Documentos/PROJAPA/artifacts/product/summary.json` | Campeão, ranking, universo e cortes do produto |
| F9 | `/home/danylo-oliveira/Documentos/PROJAPA/artifacts/category/summary.json` | 14 categorias e campeão auxiliar Linear |
| F10 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response/metrics.csv` | Comparação dos modelos de resposta ao preço |
| F11 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response/ablation_without_scenario.csv` | Avaliação sem os campos de cenário |
| F12 | `/home/danylo-oliveira/Documentos/PROJAPA/artifacts/price_response/loglog.json` | Coeficiente compartilhado e intervalo bootstrap |
| F13 | `/home/danylo-oliveira/Documentos/PROJAPA/pricing/engine.py` | Fórmula, grade, limites e desempate |
| F14 | `/home/danylo-oliveira/Documentos/PROJAPA/pricing/api.py` | Endpoints e persistência |
| F15 | `/home/danylo-oliveira/Documentos/PROJAPA/README.md` | Execução e arquitetura final |
| F16 | `/home/danylo-oliveira/Documentos/PROJAPA/reports/price_response/individual_support.csv` | Triagem e faixa de preços do produto da demonstração |
| L1 | `/home/danylo-oliveira/Documentos/PROJAPA/runtime/validation-mvp.log` e `/home/danylo-oliveira/Documentos/PROJAPA/runtime/validation-science.log` | Evidência registrada dos 41 + 11 testes |

Os relatórios científicos preservam frases relativas às etapas em que foram escritos, como “motor ainda não implementado”. Para o estado final do software, usar F4 e F15. Não apresentar essas frases históricas como pendências atuais e não editar os relatórios para preparar a apresentação.

## Regras de fidelidade para a futura montagem

- Manter 10 slides no total, sem transformar estes anexos em slides extras.
- Distinguir explicitamente MAE de seleção disponível e MAE do alvo eventual.
- Distinguir painel completo de demanda e amostra de semanas com transações do experimento de preço.
- Preservar títulos, eixos, unidades e legendas dos gráficos usados.
- Identificar prints ainda pendentes como recursos a capturar, sem fabricar telas.
- Não alegar causalidade, preço ótimo comprovado, lucro ou receita real garantida.
- Não promover a regressão polinomial ou um modelo escolhido retrospectivamente no teste.
- Manter as ressalvas econômicas junto dos cenários, além do slide de limitações.
- Não apresentar Docker como executado ou o navegador integrado como visualmente aprovado.

Este roteiro foi elaborado consultando as evidências existentes. Não altera código, modelagem, métricas ou dados do projeto.
