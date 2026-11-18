"""Testes pequenos do experimento temporal complementar; sem busca completa."""
import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.temporal_cv import experiment as cv


class TemporalCVTests(unittest.TestCase):
    def panel(self):
        weeks = pd.date_range("2017-12-04", "2018-05-07", freq="7D")
        rows = []
        for entity in ["p1", "p2"]:
            for week in weeks:
                row = {
                    "entity_id": entity,
                    "category": "c",
                    "week": week,
                    "split": cv.original.split_for(week),
                    "history_weeks": 8,
                    "target_units": 999.0,  # nunca é usado pelo CV
                }
                row.update({name: 1.0 for name in cv.original.NUM})
                row["category"] = "c"
                row["history_weeks"] = 8
                rows.append(row)
        return pd.DataFrame(rows)

    def raw(self):
        return pd.DataFrame(
            [
                {"product_id": "p1", "category": "c", "week": pd.Timestamp("2018-01-01"),
                 "purchase": pd.Timestamp("2018-01-02"), "available": pd.Timestamp("2018-01-10"),
                 "order_status": "delivered"},
                {"product_id": "p1", "category": "c", "week": pd.Timestamp("2018-01-01"),
                 "purchase": pd.Timestamp("2018-01-03"), "available": pd.Timestamp("2018-02-02"),
                 "order_status": "delivered"},
                {"product_id": "p1", "category": "c", "week": pd.Timestamp("2018-01-08"),
                 "purchase": pd.Timestamp("2018-01-09"), "available": pd.Timestamp("2018-02-03"),
                 "order_status": "delivered"},
                {"product_id": "p1", "category": "c", "week": pd.Timestamp("2018-01-15"),
                 "purchase": pd.Timestamp("2018-01-16"), "available": pd.Timestamp("2018-01-20"),
                 "order_status": "delivered"},
            ]
        )

    def test_folds_are_expanding_week_aligned_and_exclude_test(self):
        panel = self.panel()
        previous_end = None
        for fold in cv.FOLDS:
            train, validation = cv.fold_partitions(panel, fold)
            self.assertLess(train.week.max(), fold.train_cutoff)
            self.assertGreaterEqual(validation.week.min(), fold.validation_start)
            self.assertLess(validation.week.max(), fold.validation_end)
            self.assertTrue(((validation.week + pd.Timedelta(days=7)) <= fold.label_cutoff).all())
            self.assertFalse(validation.week.map(cv.original.split_for).eq("test").any())
            self.assertTrue(set(train.week).isdisjoint(validation.week))
            if previous_end is not None:
                self.assertGreaterEqual(fold.train_cutoff, previous_end)
            previous_end = fold.validation_end
        last_validation = cv.fold_partitions(panel, cv.FOLDS[-1])[1]
        self.assertNotIn(pd.Timestamp("2018-04-30"), set(last_validation.week))

    def test_censored_cohorts_are_flagged_and_true_no_purchase_is_zero(self):
        panel = self.panel()
        rows = panel[
            panel.week.isin(
                [pd.Timestamp("2018-01-01"), pd.Timestamp("2018-01-08"), pd.Timestamp("2018-01-15")]
            )
        ].copy()
        labels = cv.label_observations_as_of(self.raw(), rows, pd.Timestamp("2018-01-29"), "product")
        by_key = {
            (r.entity_id, r.week): label
            for (_, r), (_, label) in zip(rows.iterrows(), labels.iterrows())
        }
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-01"))].label_status, "censored_lower_bound")
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-01"))].label_confirmed_as_of_cutoff, 1.0)
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-08"))].label_status, "censored_lower_bound")
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-08"))].label_confirmed_as_of_cutoff, 0.0)
        self.assertEqual(by_key[("p2", pd.Timestamp("2018-01-01"))].label_status, "known_zero")
        self.assertEqual(by_key[("p2", pd.Timestamp("2018-01-01"))].label_confirmed_as_of_cutoff, 0.0)
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-15"))].label_status, "complete")
        self.assertEqual(by_key[("p1", pd.Timestamp("2018-01-15"))].label_confirmed_as_of_cutoff, 1.0)
        with self.assertRaises(ValueError):
            cv.label_observations_as_of(self.raw(), rows, pd.Timestamp("2018-01-14"), "product")

    def test_parameter_search_is_bounded_and_reproducible(self):
        first = cv.candidate_catalog(seed=42)
        second = cv.candidate_catalog(seed=42)
        self.assertEqual(first, second)
        self.assertEqual(sum(c["model"] == "RandomForest" for c in first), 8)
        self.assertEqual(sum(c["model"] == "GradientBoosting" for c in first), 8)
        self.assertEqual(
            {c["params"]["preprocess__num__poly__degree"] for c in first if c["model"] == "Polynomial"},
            {1, 2},
        )
        metadata = json.loads(json.dumps(cv.summary_metadata()))
        self.assertEqual(metadata["candidate_count"], len(first))
        self.assertIn("test", metadata["test_policy"])

    def test_test_partition_is_not_exported_by_a_reduced_run(self):
        panel = self.panel()
        candidate = next(c for c in cv.candidate_catalog() if c["model"] == "MovingAverage4")
        metrics, predictions, ranking = cv.run_cv(
            self.raw(), panel, "product", folds=(cv.FOLDS[0],), candidates=(candidate,)
        )
        self.assertEqual(set(metrics.partition), {"train", "validation"})
        self.assertEqual(set(predictions.partition), {"train", "validation"})
        self.assertTrue((ranking.model == "MovingAverage4").all())
        self.assertFalse(predictions.week.ge("2018-05-07").any())

        changed_test = panel.copy()
        changed_test.loc[changed_test.split.eq("test"), "target_units"] = -123456.0
        changed_metrics, changed_predictions, changed_ranking = cv.run_cv(
            self.raw(), changed_test, "product", folds=(cv.FOLDS[0],), candidates=(candidate,)
        )
        pd.testing.assert_frame_equal(metrics, changed_metrics)
        pd.testing.assert_frame_equal(predictions, changed_predictions)
        pd.testing.assert_frame_equal(ranking, changed_ranking)

    def test_development_panel_builder_never_passes_test_rows(self):
        raw = pd.DataFrame(
            {"week": [pd.Timestamp("2018-04-23"), pd.Timestamp("2018-05-07")]}
        )
        old_weeks = cv.original.WEEKS
        observed = {}

        def fake_make_panel(source, entities, mapping, level):
            observed["max_raw_week"] = source.week.max()
            observed["max_panel_week"] = cv.original.WEEKS.max()
            return source

        with patch.object(cv.original, "make_panel", side_effect=fake_make_panel):
            result = cv.make_development_panel(raw, ["p1"], {}, "product")

        self.assertEqual(result.week.tolist(), [pd.Timestamp("2018-04-23")])
        self.assertEqual(observed["max_raw_week"], pd.Timestamp("2018-04-23"))
        self.assertEqual(observed["max_panel_week"], pd.Timestamp("2018-04-23"))
        self.assertIs(cv.original.WEEKS, old_weeks)

    def test_pipeline_candidate_fits_only_on_fold_train_and_returns_metrics(self):
        panel = self.panel()
        candidate = next(c for c in cv.candidate_catalog() if c["model"] == "Linear")
        metrics, predictions = cv.evaluate_candidate(
            self.raw(), panel, "product", cv.FOLDS[0], candidate
        )
        self.assertEqual({r["partition"] for r in metrics}, {"train", "validation"})
        for row in metrics:
            self.assertIn("MAE", row)
            self.assertIn("RMSE", row)
            self.assertIn("R2", row)
            self.assertEqual(row["fold"], "fold_1")
        self.assertTrue(all(np.isfinite(p["prediction"]) for p in predictions))


if __name__ == "__main__":
    unittest.main()
