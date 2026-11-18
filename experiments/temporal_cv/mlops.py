"""Registra no MLflow local resultados já calculados, sem treinar modelos."""
from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "temporal_cv" / "results"
TRACKING_DIR = ROOT / "mlruns"
TRACKING_DB = TRACKING_DIR / "mlflow.db"


def _git_metadata() -> tuple[str, bool]:
    """Return HEAD and whether any tracked or untracked worktree change exists."""
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return commit, bool(status.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_./-]", "_", value)[:250]


def log_existing_results() -> int:
    """Log summary and candidate/fold results to a local file-backed store."""
    try:
        import mlflow
    except ImportError as exc:
        raise RuntimeError(
            "MLflow não está instalado; instale as dependências opcionais de "
            "requirements-mlops.txt para habilitar o rastreamento local."
        ) from exc

    required = ["summary.json", "candidate_ranking.csv", "fold_metrics.csv", "label_coverage.csv"]
    missing = [name for name in required if not (RESULTS / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Resultados necessários ausentes: {', '.join(missing)}")

    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    ranking = pd.read_csv(RESULTS / "candidate_ranking.csv")
    fold_metrics = pd.read_csv(RESULTS / "fold_metrics.csv")
    commit, dirty = _git_metadata()
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{TRACKING_DB.resolve().as_posix()}")
    experiment_name = "PROJAPA-temporal-cv-complementar"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        mlflow.create_experiment(
            experiment_name,
            artifact_location=(TRACKING_DIR / "artifacts").resolve().as_uri(),
        )
    mlflow.set_experiment(experiment_name)

    root_tags = {
        "git.commit": commit,
        "git.worktree_dirty": str(dirty).lower(),
        "record_type": "retrospective_import",
        "result_origin": "precomputed_temporal_cv_results",
        "methodology": "complementar_temporal_cv_expansiva",
        "original_selected_model": summary["currently_selected_model"],
        "retrospective_test_used": "false",
        "test_set_policy": "retrospective_test_excluded_from_selection",
        "experiment_script_sha256": _sha256(Path(__file__).with_name("experiment.py")),
        "raw_manifest_sha256": _sha256(ROOT / "data" / "raw" / "manifest.json"),
    }
    parent_params = {
        "seed": summary["seed"],
        "fold_count": len(summary["folds"]),
        "candidate_count": summary["candidate_count"],
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "mlflow_version": mlflow.__version__,
        "selection_rule": summary["selection_rule"],
        "label_definition": summary["label_definition"],
    }

    runs_logged = 0
    with mlflow.start_run(run_name="temporal_cv_results_import"):
        mlflow.set_tags(root_tags)
        mlflow.log_params({key: str(value) for key, value in parent_params.items()})
        for filename in ["summary.json", "candidate_ranking.csv", "fold_metrics.csv", "label_coverage.csv", "report.md"]:
            artifact = RESULTS / filename
            if artifact.is_file():
                mlflow.log_artifact(str(artifact), artifact_path="results")

        validations = fold_metrics[fold_metrics["partition"].eq("validation")]
        for row in ranking.itertuples(index=False):
            subset = validations[
                validations["level"].eq(row.level)
                & validations["model"].eq(row.model)
                & validations["candidate_id"].eq(row.candidate_id)
            ]
            with mlflow.start_run(
                run_name=f"{row.level}-{row.model}-{runs_logged + 1:02d}",
                nested=True,
            ):
                mlflow.set_tags(
                    {
                        **root_tags,
                        "level": str(row.level),
                        "model": str(row.model),
                        "candidate_id": str(row.candidate_id),
                    }
                )
                params = json.loads(row.params_json) if isinstance(row.params_json, str) else {}
                mlflow.log_params(
                    {
                        "seed": str(summary["seed"]),
                        "level": str(row.level),
                        "model": str(row.model),
                        **{f"candidate_{_safe_key(key)}": str(value) for key, value in params.items()},
                    }
                )
                for metric in ("MAE", "RMSE", "R2"):
                    mean_value = getattr(row, f"mean_{metric}")
                    std_value = getattr(row, f"std_{metric}")
                    if pd.notna(mean_value):
                        mlflow.log_metric(f"validation_{metric.lower()}_mean", float(mean_value))
                    if pd.notna(std_value):
                        mlflow.log_metric(f"validation_{metric.lower()}_std", float(std_value))
                for fold_row in subset.itertuples(index=False):
                    for metric in ("MAE", "RMSE", "R2"):
                        value = getattr(fold_row, metric)
                        if pd.notna(value):
                            mlflow.log_metric(
                                f"{fold_row.fold}_{metric.lower()}", float(value)
                            )
                runs_logged += 1
    return runs_logged


if __name__ == "__main__":
    count = log_existing_results()
    print(f"Resultados registrados localmente: {count} execuções de candidatos")
