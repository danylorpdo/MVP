# Finalização do MVP — 20/09/2026

## 1. Estado encontrado

Projeto existente em `/home/danylo-oliveira/Documentos/PROJAPA`. Motor, FastAPI, Streamlit, SQLite, 35 testes do MVP, Dockerfile e Compose já estavam implementados. O log `runtime/pytest.log` registrava os 35 testes aprovados. O README ainda dizia que não havia API/interface; não havia relatório de fechamento do MVP. Não foi possível inferir o instante exato da interrupção anterior apenas pelos arquivos, mas a implementação e a primeira execução de testes já haviam ocorrido.

Foram inspecionados código, contratos, testes, configuração de dependências, Docker, relatórios e manifestos/artefatos. A estrutura usa `pricing/` para o aplicativo, sem pastas separadas `src/` ou `dashboard/`.

## 2. Alterações

- `pricing/ui.py`: preserva demanda histórica zero no campo da interface; trata erros HTTP sem JSON e respostas JSON inválidas como mensagens ao usuário; trata histórico vazio sem acessar um índice inexistente.
- `pricing/api.py`: falhas SQLite na leitura de histórico/detalhes agora retornam 503 com mensagem explícita, como já ocorria na gravação.
- `tests/mvp/test_engine_api.py`: três casos adicionais de indisponibilidade SQLite, incluindo garantia de que gravação falha não seja reportada como sucesso.
- `tests/mvp/test_ui.py`: duas regressões para demanda histórica zero e recuperação após resposta de erro sem JSON.
- `tests/mvp/test_live_integration.py`: novo teste com processos reais de API e Streamlit, chamadas HTTP sem substituição, AppTest, gráficos, histórico e reinício da API.
- `README.md`: instruções atuais de instalação, execução, endpoints, testes, demonstração, artefatos exigidos, ciência e Docker.
- `docs/validacao_mvp.md`: este registro de fechamento.

Logs novos em `runtime/validation-*.log`. Nenhuma alteração em motor, schemas, modelos, métricas, dados científicos ou arquivos Docker foi necessária. O diretório `.git` acessível nesta sessão não contém um repositório funcional; portanto esta relação foi registrada pelas edições realizadas, sem alegar commit ou diff Git.

## 3. Funcionalidades finais

Catálogo de 136 produtos; demanda manual ou MovingAverage4 histórico; estoque informado; grade limitada a ±10% incluindo preço atual; comparação de receita; empate conservador; alertas de extrapolação e suporte; identificação dos artefatos; persistência SQLite; consulta de histórico; exportação JSON. A elasticidade compartilhada exata é −1,5255852107075418. Não há alegação causal nem promessa de ganho real.

Os 100 arquivos científicos registrados em `docs/science_before_mvp.json` conservam seus hashes. Os nove CSVs brutos e o ZIP também coincidem com os dez hashes do manifesto. MovingAverage4 foi preservado como campeão; não houve novo treinamento ou seleção pelo teste.

## 4. Endpoints

| Método | Rota | Resultado |
|---|---|---|
| GET | `/health` | Estado, versão e modelos |
| GET | `/api/v1/metadata` | Elasticidade, intervalo, limites e hashes |
| GET | `/api/v1/products` | 136 produtos e suporte histórico |
| GET | `/api/v1/products/{product_id}/history` | Histórico de demanda-base |
| POST | `/api/v1/simulations` | Resultado completo persistido, HTTP 201 |
| GET | `/api/v1/simulations?limit=20` | Lista de simulações |
| GET | `/api/v1/simulations/{simulation_id}` | Entrada e resultado de uma simulação |
| GET | `/docs`, `/redoc`, `/openapi.json` | Documentação automática |

## 5. Interface e integração

As páginas Simular, Histórico e Metodologia passaram pelo AppTest. Foram executados os modos manual e histórico, conferidos sete indicadores, tabela e dois gráficos, além da leitura da simulação persistida. O teste de integração sobe Uvicorn e Streamlit em portas livres, executa a interface com chamadas HTTP reais, reinicia o processo da API e verifica novamente os dois registros salvos. O banco de testes é temporário e não altera o histórico da demonstração.

Os servidores de demonstração também responderam HTTP 200 em `127.0.0.1:8000/health` e `127.0.0.1:8501/_stcore/health` ao final. O navegador integrado demorou e exibiu somente a estrutura inicial da página. Assim, há validação funcional da interface e da integração, mas não uma inspeção visual completa do navegador. Isso não foi tratado como evidência de falha do aplicativo nem como inspeção visual aprovada.

## 6. Resultados dos testes

| Verificação | Resultado |
|---|---|
| Suíte original do MVP | 35 aprovados antes das alterações |
| Suíte final do MVP | 41 aprovados em 7,41 s |
| Ciência (unittest) | 11 aprovados em 0,366 s na execução final |
| MVP em ambiente Python vazio, após instalação do requirements | 41 aprovados em 7,38 s |
| `pip check`, ambientes existentes e novo ambiente MVP | Sem dependências quebradas |
| Preservação científica | 100 hashes iguais |
| Preservação dos dados brutos | 10 hashes iguais: 9 CSVs e ZIP |

Total: **52 testes distintos aprovados**, com repetição dos 41 do MVP no ambiente recém-instalado. Uma advertência de depreciação de `BlockingPortal` vem da dependência Starlette/AnyIO; não há falha de teste. A tentativa inicial restrita travou ao iniciar TestClient; liberar rede para sockets locais resolveu, sem alteração no código científico ou nas dependências.

Evidências: `runtime/validation-mvp.log`, `validation-science.log`, `validation-clean-install.log`, `validation-clean-check.log` e `validation-clean-tests.log`.

## 7. Comandos exatos de execução

Preparação (só necessária em uma nova cópia/ambiente):

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
python3.12 -m venv .venv-app
.venv-app/bin/python -m pip install -r requirements-app.txt
```

Terminal 1:

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
.venv-app/bin/python -m uvicorn pricing.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
PRICING_API_URL=http://127.0.0.1:8000 .venv-app/bin/python -m streamlit run pricing/ui.py --server.address=127.0.0.1 --server.port=8501
```

Interface: <http://127.0.0.1:8501>. Swagger: <http://127.0.0.1:8000/docs>. Os servidores foram deixados iniciados nesta sessão; não inicie duplicatas se as portas já estiverem ocupadas.

Teste MVP: `.venv-app/bin/python -m pytest -q`. Ciência: `.venv/bin/python -m unittest discover -s tests -v`. Execute na raiz. O README descreve a instalação separada do ambiente científico e os quatro artefatos necessários para transportar o aplicativo.

## 8. Docker

Dockerfile e Compose existentes foram inspecionados: os caminhos necessários existem; API e UI compartilham imagem, a UI usa o endereço interno da API, há healthchecks e volume para SQLite, e a imagem define usuário não administrativo. **Docker não está instalado nesta máquina.** Não foi possível executar `docker compose config`, build ou contêineres. A inspeção não equivale a validação executada.

Em uma máquina com Docker Engine/Compose v2:

```bash
cd /home/danylo-oliveira/Documentos/PROJAPA
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api ui
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8501/_stcore/health
```

Pare os servidores Python antes, caso ocupem as mesmas portas. `docker compose down` mantém o volume. Não use `down -v` se quiser preservar o histórico.

## 9. Estrutura relevante

```text
PROJAPA/
├── pricing/                 API, interface, engine, schemas, artifacts, storage
├── tests/
│   ├── test_temporal_pipeline.py
│   ├── test_price_response.py
│   └── mvp/                 motor/API, UI e integração HTTP real
├── scripts/                 pipeline científico preservado
├── data/raw/                Olist e manifesto
├── data/processed/          matrizes congeladas
├── artifacts/               product, category, price_response
├── reports/                 relatórios, métricas, tabelas e figuras
├── docs/                    hashes científicos e validação do MVP
├── runtime/                 SQLite e logs
├── .streamlit/config.toml
├── Dockerfile
├── compose.yaml
├── requirements-*.txt
├── pytest.ini
└── README.md
```

## 10. Pendências reais

1. Executar o ciclo Docker/Compose em uma máquina onde Docker esteja instalado.
2. Fazer a conferência visual final no navegador usado na apresentação; o navegador integrado desta sessão ficou na estrutura inicial, apesar dos servidores e testes funcionais aprovados.

Não há defeito funcional conhecido nos fluxos testados. A ausência de validação causal de preço é uma limitação científica declarada, não uma pendência a resolver com novos modelos neste MVP.

## 11. Parecer para apresentação

**Pronto funcionalmente para demonstração acadêmica local em Python**, com 52 testes aprovados, instalação nova confirmada e evidências científicas preservadas. Antes da aula, abra a interface no navegador da apresentação e faça uma simulação manual e outra histórica. Não apresente Docker como validado até executar a pendência. Não foram criados slides.
