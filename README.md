# Motor de Precificação Dinâmica para Marketplace

**Danylo e William · Tema 7 · Mineração de Dados em Engenharia de Software**

MVP acadêmico com FastAPI, Streamlit e SQLite. Compara cenários semanais de receita para os **136 produtos recorrentes** do experimento Olist. Não altera preços reais. O campeão de previsão permanece **MovingAverage4**, escolhido na validação; o teste não é usado para escolher outro modelo.

## Executar o MVP a partir de uma cópia do projeto

Requisitos: Python **3.12**, suporte a `venv` e internet para a instalação inicial. Depois de instaladas as dependências, a demonstração funciona offline com os artefatos locais. Não é necessário treinar nem baixar novamente a Olist.

Execute na raiz da cópia do projeto; nesta máquina:

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
python3.12 -m venv .venv-app
.venv-app/bin/python -m pip install -r requirements-app.txt
.venv-app/bin/python -m pip check
```

Em outro computador, ajuste somente o caminho do `cd`. Copie também os quatro arquivos necessários ao aplicativo, pois matrizes processadas são ignoradas pelo Git:

```text
artifacts/product/chosen_model.joblib
artifacts/price_response/loglog.json
reports/price_response/individual_support.csv
data/processed/product_week_features.csv
```

A aplicação verifica o nome do campeão e calcula os hashes dos arquivos utilizados. O `.joblib` deve ser o artefato confiável produzido por este projeto. O MVP não carrega os modelos complexos nem reexecuta os experimentos.

**Terminal 1 — API:**

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
.venv-app/bin/python -m uvicorn pricing.api:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — interface:**

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
PRICING_API_URL=http://127.0.0.1:8000 .venv-app/bin/python -m streamlit run pricing/ui.py --server.address=127.0.0.1 --server.port=8501
```

Abra a interface em <http://127.0.0.1:8501> e a documentação interativa em <http://127.0.0.1:8000/docs>. Encerre cada servidor com `Ctrl+C`. Se uma porta estiver ocupada, altere `--port`/`--server.port`; ao mudar a porta da API, atualize também `PRICING_API_URL`.

O banco padrão é `runtime/simulations.sqlite`. A API cria a pasta e a tabela automaticamente. `PRICING_DB_PATH` permite escolher outro arquivo. O histórico permanece após reinícios. Para copiar um backup simples, pare a API antes de copiar o banco. Os testes usam bancos temporários.

## Demonstração pela interface

1. Em **Simular**, escolha um produto; a tela mostra ID, categoria e faixa de preços do treino.
2. Confirme o preço atual e informe o estoque. Os valores iniciais são exemplos editáveis; o preço sugerido no campo vem do histórico, e o estoque inicial 20 é apenas um parâmetro de demonstração, não um dado da Olist.
3. Escolha demanda semanal manual ou **MovingAverage4 histórico**, com uma semana de referência. Uma semana antiga não representa uma previsão para hoje. A demanda histórica zero é preservada.
4. Clique em **Comparar preços**. Veja preço recomendado no cenário, variação, demanda, unidades vendáveis, receitas comparativas, avisos, dois gráficos e tabela de candidatos. Baixe o resultado em JSON se necessário.
5. Em **Histórico**, abra uma simulação persistida. Em **Metodologia**, consulte fórmula e limitações. As versões e hashes também aparecem nos resultados.

Para demonstrar o papel do estoque, use preço R$ 100 e demanda manual 10: com estoque 100, o candidato R$ 90 maximiza a receita estimada da grade; com estoque 2, o candidato R$ 110 é selecionado. São consequências da hipótese adotada, não ganhos empiricamente comprovados. Com estoque ou demanda zero, o empate preserva o preço atual.

## Motor e limitações científicas

```text
base = MovingAverage4 histórico OU demanda semanal manual
fator = (preço candidato / preço atual) ** beta
demanda ajustada = base × fator
unidades vendáveis = min(demanda ajustada, estoque informado)
receita estimada = preço candidato × unidades vendáveis
```

`beta = -1.5255852107075418`, lido do artefato log-log compartilhado (aproximadamente −1,526). A grade padrão é −10%, −5%, 0%, +5%, +10%; redução/aumento podem ser ajustados até 10%, com passo mínimo 0,1%. Preços são arredondados para centavos sem ultrapassar os limites. O preço atual sempre participa. Empates de receita em centavos preferem a menor alteração.

A elasticidade é **associativa e experimental**, estimada em semanas com vendas. Aplicá-la à demanda-base de todas as semanas é uma hipótese não validada. Não há estoque, concorrência, custos, exposição ou demanda não atendida observados. Receita não é lucro; unidades fracionárias são expectativas. Somente 35 produtos passam a triagem de suporte individual e isso não valida elasticidade individual. Todos usam o mesmo fator compartilhado. Extrapolações e suporte insuficiente são sinalizados, inclusive quando o candidato recomendado fica fora da faixa histórica.

Os relatórios científicos preservam a descrição da etapa em que foram escritos, inclusive frases como “API ainda não implementada”. O estado atual de software está neste README e em `docs/validacao_mvp.md`.

## API

| Método | Rota | Função |
|---|---|---|
| GET | `/health` | Estado da API e conexão SQLite |
| GET | `/api/v1/metadata` | Elasticidade, intervalo, versões e limites |
| GET | `/api/v1/products` | Catálogo dos 136 produtos |
| GET | `/api/v1/products/{product_id}/history` | Semanas e demanda-base disponíveis |
| POST | `/api/v1/simulations` | Calcula e salva; retorna HTTP 201 |
| GET | `/api/v1/simulations?limit=20` | Histórico recente, limite de 1 a 100 |
| GET | `/api/v1/simulations/{simulation_id}` | Entrada original e resultado salvo |
| GET | `/docs`, `/redoc`, `/openapi.json` | Documentação e contrato |

Exemplo de corpo para `POST /api/v1/simulations` (use um ID do catálogo):

```json
{
  "product_id": "060cb19345d90064d1015407193c233d",
  "current_price": 100.00,
  "stock": 20,
  "demand_source": "manual",
  "base_demand": 10,
  "max_decrease_pct": 10,
  "max_increase_pct": 10,
  "step_pct": 5
}
```

No modo `moving_average4`, omita `base_demand`. `reference_week`, no formato `AAAA-MM-DD`, é opcional: quando ausente, usa a última semana disponível. Estoque deve ser inteiro não negativo; preço deve ser positivo e ter até duas casas decimais. Campos desconhecidos são rejeitados. Entradas inválidas retornam 422, produto/simulação inexistente retorna 404, e falhas SQLite durante gravação/consulta retornam 503.

A resposta inclui preço atual/recomendado, variação, demanda-base/ajustada, estoque, unidades vendáveis, ambas as receitas, cenários, avisos, faixa histórica, semana de referência, elasticidade, versões/hashes, ID e horário UTC.

## Testes

Os ambientes são separados porque os experimentos congelados usam versões diferentes de NumPy/pandas e dependem de scikit-learn. Não misture os dois arquivos de dependências.

```bash
# MVP: motor, API, SQLite, interface e integração HTTP real
.venv-app/bin/python -m pytest -q

# Ciência: todos os 11 testes anteriores, sem reexecutar treinamento
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-modeling.txt
.venv/bin/python -m unittest discover -s tests -v
```

`pytest.ini` seleciona `tests/mvp`; o comando de unittest cobre os testes científicos da raiz de `tests`. Execute **ambos** para verificar tudo. O teste HTTP abre portas livres em localhost, inicia API/Streamlit, usa AppTest sem substituir as chamadas HTTP, verifica gráficos e reinicia a API para conferir persistência. Precisa de permissão para sockets locais. Não deixa servidores nem simulações de teste no banco da demonstração.

## Docker / Compose

São fornecidos `Dockerfile` e `compose.yaml`. Requer Docker Engine e Compose v2 disponíveis. A imagem instala somente as dependências do MVP e copia seus quatro artefatos; executa com usuário sem privilégios administrativos. O Compose liga a interface à API por `http://api:8000`, aguarda o healthcheck da API e mantém SQLite no volume `simulation_data`.

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api ui
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8501/_stcore/health
# Parar preservando as simulações:
docker compose down
```

Use os mesmos endereços locais 8000/8501. Pare antes os servidores locais que ocupem essas portas. `docker compose down -v` apaga o volume e seu histórico; não é necessário para uso normal.

**Limite da validação:** Docker não estava instalado na máquina de finalização. Configuração e caminhos foram inspecionados, mas build, healthchecks e persistência dentro dos contêineres ainda precisam ser executados em uma máquina com Docker. A demonstração local Python foi validada separadamente.

## Evidências e estrutura

```text
pricing/                    motor, catálogo, schemas, API, SQLite, Streamlit
scripts/                    aquisição, validação, modelagem e relatórios científicos
tests/                     testes científicos
tests/mvp/                 testes do aplicativo e integração HTTP
data/raw/                  9 CSVs, ZIP e manifesto de hashes Olist
data/processed/            matrizes temporais congeladas
artifacts/product/         campeão MovingAverage4 e evidências do benchmark
artifacts/category/        experimento auxiliar
artifacts/price_response/  associação histórica e modelos experimentais
reports/                   viabilidade, modelagem, métricas e gráficos
docs/science_before_mvp.json  hashes de preservação científica
docs/validacao_mvp.md       resultados da finalização
runtime/                   SQLite e logs locais (fora do versionamento)
Dockerfile, compose.yaml   empacotamento do MVP
requirements-*.txt         dependências por etapa
```

O fluxo CRISP-DM está documentado em `reports/viabilidade_dataset.md` (negócio, aquisição, qualidade e limitações), `reports/modelagem.md` (preparação temporal, comparação e avaliação), `reports/price_response.md` (experimento associativo separado) e neste README (integração e demonstração). Treino 2017, validação janeiro–abril/2018, teste maio–agosto/2018; nenhuma decisão científica foi substituída nesta finalização.

Para reproduzir a pesquisa em uma **cópia separada**, consulte os relatórios e os scripts `download_olist.py`, `validate_olist.py`, `modeling.py`, `report_modeling.py`, `price_response.py`, `report_price_response.py`. Eles podem regenerar arquivos e não são necessários para iniciar o MVP. Preserve as evidências originais e o ZIP/hash do dataset; um novo download público pode ter outra versão.
