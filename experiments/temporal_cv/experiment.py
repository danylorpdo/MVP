"""Busca temporal expansiva complementar ao benchmark científico original.

O alvo usado em cada corte é o número de itens já confirmados como entregues
naquele corte. É uma fotografia censurada do alvo eventual: nenhuma entrega
futura é imputada como zero no alvo eventual, e semanas posteriores ao corte
nunca são pontuadas.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterSampler

from scripts import modeling as original


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
SEED = 42
WARMUP_WEEKS = 4
WEEK_DAYS = 7
TEST_START = pd.Timestamp("2018-05-07")


@dataclass(frozen=True)
class TemporalFold:
    name: str
    train_cutoff: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    label_cutoff: pd.Timestamp


FOLDS = (
    TemporalFold("fold_1", pd.Timestamp("2018-01-01"), pd.Timestamp("2018-01-01"), pd.Timestamp("2018-01-29"), pd.Timestamp("2018-01-29")),
    TemporalFold("fold_2", pd.Timestamp("2018-01-29"), pd.Timestamp("2018-01-29"), pd.Timestamp("2018-02-26"), pd.Timestamp("2018-02-26")),
    TemporalFold("fold_3", pd.Timestamp("2018-02-26"), pd.Timestamp("2018-02-26"), pd.Timestamp("2018-03-26"), pd.Timestamp("2018-03-26")),
    TemporalFold("fold_4", pd.Timestamp("2018-03-26"), pd.Timestamp("2018-03-26"), pd.Timestamp("2018-05-01"), pd.Timestamp("2018-05-01")),
)


def _json_params(params: dict) -> str:
    return json.dumps(params, sort_keys=True, separators=(",", ":"))


def _candidate(model: str, params: dict | None = None) -> dict:
    params = params or {}
    return {
        "model": model,
        "params": params,
        "params_json": _json_params(params),
        "candidate_id": f"{model}:{_json_params(params)}",
    }


def candidate_catalog(seed: int = SEED) -> list[dict]:
    """Return fixed references plus a bounded, reproducible search space."""
    candidates = [
        _candidate("PreviousWeek"),
        _candidate("MovingAverage4"),
        _candidate("Linear"),
        *[_candidate("Polynomial", {"preprocess__num__poly__degree": degree}) for degree in (1, 2)],
    ]

    rf_space = {
        "regressor__n_estimators": [100, 200, 400],
        "regressor__max_depth": [4, 8, None],
        "regressor__min_samples_leaf": [2, 5, 10],
        "regressor__max_features": [0.5, 1.0],
    }
    gb_space = {
        "regressor__n_estimators": [100, 150, 250],
        "regressor__learning_rate": [0.03, 0.05, 0.1],
        "regressor__max_depth": [1, 2, 3],
        "regressor__min_samples_leaf": [5, 10, 20],
    }
    # ParameterSampler is seeded and capped at eight combinations per family.
    for model_name, space in (("RandomForest", rf_space), ("GradientBoosting", gb_space)):
        for params in ParameterSampler(space, n_iter=8, random_state=seed):
            candidates.append(_candidate(model_name, dict(params)))
    return candidates


def fold_partitions(panel: pd.DataFrame, fold: TemporalFold) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select whole-week expanding train and validation partitions.

    The validation partition is restricted to the original validation window;
    in particular, the 2018-04-30 boundary week and the retrospective test are
    excluded.
    """
    weeks = pd.to_datetime(panel["week"])
    full_week_end = weeks + pd.Timedelta(days=WEEK_DAYS)
    warmed = panel["history_weeks"].ge(WARMUP_WEEKS)
    train_mask = warmed & full_week_end.le(fold.train_cutoff)
    validation_mask = (
        warmed
        & weeks.ge(fold.validation_start)
        & weeks.lt(fold.validation_end)
        & full_week_end.le(fold.label_cutoff)
        & weeks.map(original.split_for).eq("validation")
    )

    train = panel.loc[train_mask].copy()
    validation = panel.loc[validation_mask].copy()
    if train.empty or validation.empty:
        raise ValueError(f"{fold.name} gerou partição vazia")
    if (train.week >= fold.train_cutoff).any():
        raise AssertionError("Treino contém semana na origem ou no futuro")
    if (validation.week < fold.validation_start).any() or (validation.week >= fold.validation_end).any():
        raise AssertionError("Validação fora dos limites do fold")
    if (validation.week + pd.Timedelta(days=WEEK_DAYS) > fold.label_cutoff).any():
        raise AssertionError("Validação contém semana incompleta no corte dos rótulos")
    if validation.week.map(original.split_for).eq("test").any():
        raise AssertionError("O conjunto de teste retrospectivo entrou na validação")
    if set(train.week).intersection(validation.week):
        raise AssertionError("Uma semana foi dividida entre treino e validação")
    return train, validation


def label_observations_as_of(
    raw: pd.DataFrame,
    rows: pd.DataFrame,
    cutoff: pd.Timestamp,
    level: str,
) -> pd.DataFrame:
    """Separate known structural zeros, complete counts, and censored counts.

    ``label_confirmed_as_of_cutoff`` is the exact count of confirmations seen
    by the cutoff. If purchases exist but not all are confirmed, that count is
    a lower bound on the eventual target and ``label_status`` is censored; it
    must not be interpreted as zero eventual demand. A true structural zero
    is only assigned when the purchase cohort itself is empty.
    """
    if level not in {"product", "category"}:
        raise ValueError("level deve ser 'product' ou 'category'")
    if rows.empty:
        return pd.DataFrame(
            columns=["label_confirmed_as_of_cutoff", "label_status", "purchases_in_week"],
            index=rows.index,
        )

    weeks = pd.to_datetime(rows["week"])
    if (weeks + pd.Timedelta(days=WEEK_DAYS) > cutoff).any():
        raise ValueError("Rótulo solicitado antes do fechamento da semana")

    key = "product_id" if level == "product" else "category"
    entity_col = "entity_id"
    if rows.duplicated([entity_col, "week"]).any():
        raise ValueError("Esperada uma linha por entidade e semana")

    purchases = raw.groupby([key, "week"], sort=False).size()
    observed = original.known_deliveries(raw, cutoff)
    confirmed = observed.groupby([key, "week"], sort=False).size()
    lookup = pd.MultiIndex.from_arrays(
        [rows[entity_col].to_numpy(), weeks.to_numpy()], names=[key, "week"]
    )
    purchase_counts = purchases.reindex(lookup, fill_value=0).to_numpy(dtype="int64")
    confirmed_counts = confirmed.reindex(lookup, fill_value=0).to_numpy(dtype="int64")
    status = np.where(
        purchase_counts == 0,
        "known_zero",
        np.where(purchase_counts == confirmed_counts, "complete", "censored_lower_bound"),
    )
    return pd.DataFrame(
        {
            "label_confirmed_as_of_cutoff": confirmed_counts.astype("float64"),
            "label_status": status,
            "purchases_in_week": purchase_counts,
        },
        index=rows.index,
    )


def _estimator_for(candidate: dict):
    model_name = candidate["model"]
    if model_name in {"PreviousWeek", "MovingAverage4"}:
        return None
    estimator = original.model_pipeline(model_name)
    if candidate["params"]:
        estimator.set_params(**candidate["params"])
    return estimator


def _predict(candidate: dict, rows: pd.DataFrame, estimator) -> np.ndarray:
    if candidate["model"] == "PreviousWeek":
        values = rows["units_lag_1"].to_numpy(dtype="float64")
    elif candidate["model"] == "MovingAverage4":
        values = rows["units_mean_4w"].to_numpy(dtype="float64")
    else:
        values = estimator.predict(rows[original.FEATURES])
    return np.maximum(np.asarray(values, dtype="float64"), 0.0)


def evaluate_candidate(
    raw: pd.DataFrame,
    panel: pd.DataFrame,
    level: str,
    fold: TemporalFold,
    candidate: dict,
) -> tuple[list[dict], list[dict]]:
    train, validation = fold_partitions(panel, fold)
    if set(original.FEATURES).intersection(
        {"target_units", "label_available_train", "label_available_selection", "no_recorded_sale"}
    ):
        raise AssertionError("Uma coluna de rótulo/avaliação foi incluída nas features")

    train_labels = label_observations_as_of(raw, train, fold.train_cutoff, level)
    validation_labels = label_observations_as_of(raw, validation, fold.label_cutoff, level)
    y_train = train_labels["label_confirmed_as_of_cutoff"]
    y_validation = validation_labels["label_confirmed_as_of_cutoff"]
    estimator = _estimator_for(candidate)
    if estimator is not None:
        # Imputação, escala e codificação ficam no Pipeline e são ajustadas
        # exclusivamente nas linhas de treino deste fold.
        estimator.fit(train[original.FEATURES], y_train)

    metric_rows: list[dict] = []
    prediction_rows: list[dict] = []
    for partition, rows, labels, observations, cutoff in (
        ("train", train, y_train, train_labels, fold.train_cutoff),
        ("validation", validation, y_validation, validation_labels, fold.label_cutoff),
    ):
        predictions = _predict(candidate, rows, estimator)
        stats = original.metric(labels, predictions)
        metric_rows.append(
            {
                "level": level,
                "model": candidate["model"],
                "candidate_id": candidate["candidate_id"],
                "params_json": candidate["params_json"],
                "fold": fold.name,
                "partition": partition,
                "train_cutoff": fold.train_cutoff.date().isoformat(),
                "validation_start": fold.validation_start.date().isoformat(),
                "validation_end_exclusive": fold.validation_end.date().isoformat(),
                "label_cutoff": cutoff.date().isoformat(),
                "n": len(rows),
                "n_censored": int(observations.label_status.eq("censored_lower_bound").sum()),
                "n_known_zero": int(observations.label_status.eq("known_zero").sum()),
                "weeks": int(rows.week.nunique()),
                "MAE": stats["MAE"],
                "RMSE": stats["RMSE"],
                "R2": stats["R2"],
            }
        )
        for position, (_, row) in enumerate(rows.iterrows()):
            prediction_rows.append(
                {
                    "level": level,
                    "candidate_id": candidate["candidate_id"],
                    "model": candidate["model"],
                    "params_json": candidate["params_json"],
                    "fold": fold.name,
                    "partition": partition,
                    "entity_id": row.entity_id,
                    "category": row.category,
                    "week": pd.Timestamp(row.week).date().isoformat(),
                    "label_cutoff": cutoff.date().isoformat(),
                    "label_confirmed_as_of_cutoff": float(labels.iloc[position]),
                    "label_status": observations.label_status.iloc[position],
                    "purchases_in_week": int(observations.purchases_in_week.iloc[position]),
                    "prediction": float(predictions[position]),
                }
            )
    return metric_rows, prediction_rows


def rank_candidates(metrics: pd.DataFrame) -> pd.DataFrame:
    """Rank by mean validation MAE, then mean validation RMSE, deterministically."""
    validation = metrics.loc[metrics.partition.eq("validation")].copy()
    grouped = validation.groupby(
        ["level", "model", "candidate_id", "params_json"], sort=False, dropna=False
    )
    ranking = grouped.agg(
        folds=("fold", "nunique"),
        validation_total=("n", "sum"),
        validation_censored=("n_censored", "sum"),
        validation_known_zero=("n_known_zero", "sum"),
        mean_MAE=("MAE", "mean"),
        std_MAE=("MAE", "std"),
        mean_RMSE=("RMSE", "mean"),
        std_RMSE=("RMSE", "std"),
        mean_R2=("R2", "mean"),
        std_R2=("R2", "std"),
    ).reset_index()
    return ranking.sort_values(
        ["level", "mean_MAE", "mean_RMSE", "model", "params_json"],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)


def make_development_panel(
    raw: pd.DataFrame, entities: list[str], mapping: dict, level: str
) -> pd.DataFrame:
    """Build only pre-test weeks and rows, leaving retrospective test untouched."""
    development_raw = raw.loc[raw.week.lt(TEST_START)].copy()
    original_weeks = original.WEEKS
    try:
        original.WEEKS = original_weeks[
            (original_weeks < TEST_START)
            & (original_weeks + pd.Timedelta(days=WEEK_DAYS) <= original.SELECT_AT)
        ]
        return original.make_panel(development_raw, entities, mapping, level)
    finally:
        original.WEEKS = original_weeks


def label_coverage(raw: pd.DataFrame, panel: pd.DataFrame, level: str) -> pd.DataFrame:
    """Count complete versus censored labels per fold before fitting anything."""
    rows_out = []
    for fold in FOLDS:
        train, validation = fold_partitions(panel, fold)
        for partition, rows, cutoff in (
            ("train", train, fold.train_cutoff),
            ("validation", validation, fold.label_cutoff),
        ):
            labels = label_observations_as_of(raw, rows, cutoff, level)
            rows_out.append(
                {
                    "level": level,
                    "fold": fold.name,
                    "partition": partition,
                    "cutoff": cutoff.date().isoformat(),
                    "n_total": len(labels),
                    "n_known_zero": int(labels.label_status.eq("known_zero").sum()),
                    "n_complete_positive": int(labels.label_status.eq("complete").sum()),
                    "n_censored": int(labels.label_status.eq("censored_lower_bound").sum()),
                    "n_weeks": int(rows.week.nunique()),
                }
            )
    return pd.DataFrame(rows_out)


def run_cv(
    raw: pd.DataFrame,
    panel: pd.DataFrame,
    level: str,
    folds: Iterable[TemporalFold] = FOLDS,
    candidates: Iterable[dict] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run only expanding validation folds; no test rows or targets are read."""
    chosen_candidates = list(candidates if candidates is not None else candidate_catalog())
    metric_rows: list[dict] = []
    prediction_rows: list[dict] = []
    for fold in folds:
        for candidate in chosen_candidates:
            fold_metrics, fold_predictions = evaluate_candidate(raw, panel, level, fold, candidate)
            metric_rows.extend(fold_metrics)
            prediction_rows.extend(fold_predictions)
    metrics = pd.DataFrame(metric_rows)
    predictions = pd.DataFrame(prediction_rows)
    return metrics, predictions, rank_candidates(metrics)


def write_report(ranking: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Validação temporal e busca complementar",
        "",
        "Experimento suplementar; não altera o benchmark original nem o artefato MovingAverage4.",
        "A seleção usa exclusivamente os quatro folds temporais de validação. O teste retrospectivo de maio a agosto de 2018 não é carregado, pontuado ou usado na busca.",
        "",
        "O rótulo medido é a contagem confirmada até o corte. Coortes com compras pendentes ficam marcadas como censuradas: sua contagem é um limite inferior, não demanda eventual zero. Zero estrutural só ocorre quando não houve compra naquela entidade-semana.",
        "",
        "## Busca ordenada por MAE médio de validação",
        "",
        "| Nível | Modelo | Folds | Validação (total/censurados/zeros conhecidos) | MAE médio (DP) | RMSE médio (DP) | R² médio (DP) | Parâmetros |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in ranking.itertuples(index=False):
        lines.append(
            f"| {row.level} | {row.model} | {row.folds} | "
            f"{row.validation_total}/{row.validation_censored}/{row.validation_known_zero} | "
            f"{row.mean_MAE:.6g} ({row.std_MAE:.6g}) | "
            f"{row.mean_RMSE:.6g} ({row.std_RMSE:.6g}) | "
            f"{row.mean_R2:.6g} ({row.std_R2:.6g}) | `{row.params_json}` |"
        )
    lines.extend(
        [
            "",
            "MAE é o critério primário; RMSE desempata. R² é apenas diagnóstico. O modelo atualmente selecionado continua sendo MovingAverage4 até revisão posterior explícita.",
            "",
            "O teste retrospectivo já foi inspecionado no relatório científico original; portanto, não é um holdout cego para alegações independentes de generalização.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summary_metadata() -> dict:
    return {
        "experiment": "temporal_cv_complementary",
        "seed": SEED,
        "currently_selected_model": "MovingAverage4",
        "selection_rule": "mean validation MAE across folds; mean validation RMSE tie-break; deterministic model/parameter ordering",
        "label_definition": "confirmed delivered count by label_cutoff; cohorts with unconfirmed purchases are flagged censored lower bounds; structural zero only when no purchase occurred",
        "test_policy": "retrospective test (2018-05-07 onward) excluded from fold construction, fitting, ranking, and exports",
        "test_start_excluded": TEST_START.date().isoformat(),
        "folds": [
            {
                "name": fold.name,
                "train_cutoff": fold.train_cutoff.date().isoformat(),
                "validation_start": fold.validation_start.date().isoformat(),
                "validation_end_exclusive": fold.validation_end.date().isoformat(),
                "label_cutoff": fold.label_cutoff.date().isoformat(),
            }
            for fold in FOLDS
        ],
        "candidate_count": len(candidate_catalog()),
        "results": {
            "metrics_csv": "fold_metrics.csv",
            "predictions_csv": "fold_predictions.csv",
            "ranking_csv": "candidate_ranking.csv",
            "label_coverage_csv": "label_coverage.csv",
            "report_markdown": "report.md",
        },
    }


def run_experiment() -> dict:
    """Load local source data and write the complete search outputs.

    This function is intentionally not run by tests. It requires the ignored
    Olist source CSVs and performs the full search.
    """
    raw = original.load_raw()
    products, categories, mapping = original.select_entities(raw)
    all_panels = {
        level: make_development_panel(raw, entities, mapping, level)
        for level, entities in (("product", products), ("category", categories))
    }
    coverage = pd.concat(
        [label_coverage(raw, panel, level) for level, panel in all_panels.items()],
        ignore_index=True,
    )
    all_metrics: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_rankings: list[pd.DataFrame] = []
    for level, panel in all_panels.items():
        metrics, predictions, ranking = run_cv(raw, panel, level)
        all_metrics.append(metrics)
        all_predictions.append(predictions)
        all_rankings.append(ranking)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics = pd.concat(all_metrics, ignore_index=True)
    predictions = pd.concat(all_predictions, ignore_index=True)
    ranking = pd.concat(all_rankings, ignore_index=True)
    metrics.to_csv(RESULTS_DIR / "fold_metrics.csv", index=False)
    predictions.to_csv(RESULTS_DIR / "fold_predictions.csv", index=False)
    ranking.to_csv(RESULTS_DIR / "candidate_ranking.csv", index=False)
    coverage.to_csv(RESULTS_DIR / "label_coverage.csv", index=False)
    report_path = RESULTS_DIR / "report.md"
    write_report(ranking, report_path)

    metadata = summary_metadata()
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2, ensure_ascii=False))
