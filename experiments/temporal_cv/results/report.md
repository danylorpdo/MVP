# Validação temporal e busca complementar

Experimento suplementar; não altera o benchmark original nem o artefato MovingAverage4.
A seleção usa exclusivamente os quatro folds temporais de validação. O teste retrospectivo de maio a agosto de 2018 não é carregado, pontuado ou usado na busca.

O rótulo medido é a contagem confirmada até o corte. Coortes com compras pendentes ficam marcadas como censuradas: sua contagem é um limite inferior, não demanda eventual zero. Zero estrutural só ocorre quando não houve compra naquela entidade-semana.

## Busca ordenada por MAE médio de validação

| Nível | Modelo | Folds | Validação (total/censurados/zeros conhecidos) | MAE médio (DP) | RMSE médio (DP) | R² médio (DP) | Parâmetros |
|---|---|---:|---:|---:|---:|---:|---|
| product | PreviousWeek | 4 | 2312/487/1513 | 0.526838 (0.0411688) | 1.52304 (0.133826) | -0.119188 (0.0186596) | `{}` |
| product | MovingAverage4 | 4 | 2312/487/1513 | 0.586558 (0.0748137) | 1.26381 (0.160705) | 0.228905 (0.109248) | `{}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.663872 (0.0488257) | 1.31507 (0.131054) | 0.15937 (0.134787) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":150}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.672358 (0.175798) | 1.32497 (0.161125) | 0.143796 (0.190751) | `{"regressor__learning_rate":0.1,"regressor__max_depth":2,"regressor__min_samples_leaf":20,"regressor__n_estimators":150}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.675641 (0.0465468) | 1.31732 (0.131892) | 0.156216 (0.138302) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":5,"regressor__n_estimators":150}` |
| product | Polynomial | 4 | 2312/487/1513 | 0.677054 (0.302097) | 1.50782 (0.0919355) | -0.116392 (0.233125) | `{"preprocess__num__poly__degree":2}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.679896 (0.0663218) | 1.31553 (0.131058) | 0.156438 (0.156824) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":10,"regressor__n_estimators":200}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.682066 (0.0646598) | 1.30084 (0.14351) | 0.175016 (0.163941) | `{"regressor__max_depth":null,"regressor__max_features":0.5,"regressor__min_samples_leaf":10,"regressor__n_estimators":400}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.684737 (0.0702056) | 1.32729 (0.142736) | 0.141492 (0.167827) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":200}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.685521 (0.0755916) | 1.33242 (0.151532) | 0.132281 (0.194518) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.701272 (0.115486) | 1.30784 (0.19445) | 0.167302 (0.20349) | `{"regressor__learning_rate":0.03,"regressor__max_depth":3,"regressor__min_samples_leaf":10,"regressor__n_estimators":150}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.710062 (0.093673) | 1.30693 (0.1367) | 0.168589 (0.151641) | `{"regressor__learning_rate":0.03,"regressor__max_depth":2,"regressor__min_samples_leaf":5,"regressor__n_estimators":150}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.723913 (0.0736347) | 1.32445 (0.181604) | 0.138247 (0.244091) | `{"regressor__max_depth":8,"regressor__max_features":0.5,"regressor__min_samples_leaf":2,"regressor__n_estimators":200}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.758989 (0.0700882) | 1.29266 (0.152415) | 0.188118 (0.150904) | `{"regressor__learning_rate":0.03,"regressor__max_depth":3,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| product | Linear | 4 | 2312/487/1513 | 0.771563 (0.193404) | 1.34707 (0.158417) | 0.113898 (0.197698) | `{}` |
| product | Polynomial | 4 | 2312/487/1513 | 0.771563 (0.193404) | 1.34707 (0.158417) | 0.113898 (0.197698) | `{"preprocess__num__poly__degree":1}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.786336 (0.0436023) | 1.33039 (0.115133) | 0.140431 (0.114204) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":100}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.830106 (0.0439303) | 1.34714 (0.115382) | 0.116347 (0.139561) | `{"regressor__max_depth":4,"regressor__max_features":1.0,"regressor__min_samples_leaf":10,"regressor__n_estimators":400}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.838302 (0.0490932) | 1.36388 (0.121113) | 0.0908771 (0.174345) | `{"regressor__max_depth":4,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| product | RandomForest | 4 | 2312/487/1513 | 0.84511 (0.0530669) | 1.34058 (0.115597) | 0.127058 (0.117642) | `{"regressor__max_depth":4,"regressor__max_features":0.5,"regressor__min_samples_leaf":5,"regressor__n_estimators":400}` |
| product | GradientBoosting | 4 | 2312/487/1513 | 0.928508 (0.0426125) | 1.35624 (0.111795) | 0.10919 (0.082088) | `{"regressor__learning_rate":0.03,"regressor__max_depth":1,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| category | MovingAverage4 | 4 | 238/238/0 | 28.4484 (2.61348) | 37.1614 (1.7519) | 0.196847 (0.102926) | `{}` |
| category | GradientBoosting | 4 | 238/238/0 | 29.1224 (1.78721) | 37.743 (1.08511) | 0.171574 (0.0947756) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":100}` |
| category | GradientBoosting | 4 | 238/238/0 | 29.7665 (2.65694) | 37.6941 (2.48554) | 0.175467 (0.0927283) | `{"regressor__learning_rate":0.03,"regressor__max_depth":1,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| category | Linear | 4 | 238/238/0 | 30.2859 (5.62141) | 39.6748 (6.19584) | 0.0384068 (0.445728) | `{}` |
| category | Polynomial | 4 | 238/238/0 | 30.2859 (5.62141) | 39.6748 (6.19584) | 0.0384068 (0.445728) | `{"preprocess__num__poly__degree":1}` |
| category | GradientBoosting | 4 | 238/238/0 | 30.5186 (3.49281) | 39.465 (1.2915) | 0.0895045 (0.155708) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":10,"regressor__n_estimators":150}` |
| category | GradientBoosting | 4 | 238/238/0 | 30.5186 (3.49281) | 39.465 (1.2915) | 0.0895045 (0.155708) | `{"regressor__learning_rate":0.05,"regressor__max_depth":1,"regressor__min_samples_leaf":5,"regressor__n_estimators":150}` |
| category | RandomForest | 4 | 238/238/0 | 32.556 (3.34117) | 41.7618 (2.42026) | -0.0215467 (0.206676) | `{"regressor__max_depth":null,"regressor__max_features":0.5,"regressor__min_samples_leaf":10,"regressor__n_estimators":400}` |
| category | RandomForest | 4 | 238/238/0 | 32.8794 (3.60787) | 42.746 (3.214) | -0.069559 (0.218434) | `{"regressor__max_depth":4,"regressor__max_features":1.0,"regressor__min_samples_leaf":10,"regressor__n_estimators":400}` |
| category | GradientBoosting | 4 | 238/238/0 | 32.8925 (6.52445) | 43.7109 (4.25755) | -0.111777 (0.191284) | `{"regressor__learning_rate":0.03,"regressor__max_depth":2,"regressor__min_samples_leaf":5,"regressor__n_estimators":150}` |
| category | RandomForest | 4 | 238/238/0 | 32.9504 (4.09049) | 42.9817 (3.44215) | -0.0802509 (0.213592) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":10,"regressor__n_estimators":200}` |
| category | RandomForest | 4 | 238/238/0 | 33.1895 (4.54269) | 43.6466 (4.18883) | -0.119956 (0.2683) | `{"regressor__max_depth":4,"regressor__max_features":0.5,"regressor__min_samples_leaf":5,"regressor__n_estimators":400}` |
| category | GradientBoosting | 4 | 238/238/0 | 33.5426 (6.49807) | 45.6436 (5.90145) | -0.209705 (0.240183) | `{"regressor__learning_rate":0.03,"regressor__max_depth":3,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| category | RandomForest | 4 | 238/238/0 | 33.6477 (5.39151) | 44.907 (4.9151) | -0.183034 (0.276599) | `{"regressor__max_depth":4,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| category | RandomForest | 4 | 238/238/0 | 34.9233 (6.07525) | 46.5216 (5.37636) | -0.271622 (0.309304) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":100}` |
| category | RandomForest | 4 | 238/238/0 | 35.1873 (6.31788) | 46.8007 (5.85591) | -0.287533 (0.324742) | `{"regressor__max_depth":null,"regressor__max_features":1.0,"regressor__min_samples_leaf":5,"regressor__n_estimators":200}` |
| category | GradientBoosting | 4 | 238/238/0 | 35.4329 (7.90889) | 47.1277 (6.57868) | -0.296583 (0.306558) | `{"regressor__learning_rate":0.03,"regressor__max_depth":3,"regressor__min_samples_leaf":10,"regressor__n_estimators":150}` |
| category | GradientBoosting | 4 | 238/238/0 | 35.599 (7.38988) | 45.9356 (5.19766) | -0.236854 (0.282559) | `{"regressor__learning_rate":0.1,"regressor__max_depth":2,"regressor__min_samples_leaf":20,"regressor__n_estimators":150}` |
| category | RandomForest | 4 | 238/238/0 | 36.2509 (8.01163) | 48.2925 (7.07052) | -0.374768 (0.38664) | `{"regressor__max_depth":8,"regressor__max_features":0.5,"regressor__min_samples_leaf":2,"regressor__n_estimators":200}` |
| category | PreviousWeek | 4 | 238/238/0 | 45.525 (8.76487) | 60.7004 (7.56377) | -1.14056 (0.418376) | `{}` |
| category | Polynomial | 4 | 238/238/0 | 48.1492 (11.907) | 62.6141 (11.4236) | -1.27277 (0.620801) | `{"preprocess__num__poly__degree":2}` |

MAE é o critério primário; RMSE desempata. R² é apenas diagnóstico. O modelo atualmente selecionado continua sendo MovingAverage4 até revisão posterior explícita.

O teste retrospectivo já foi inspecionado no relatório científico original; portanto, não é um holdout cego para alegações independentes de generalização.
