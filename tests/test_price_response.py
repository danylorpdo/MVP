"""Testes exclusivos da etapa independente de resposta ao preço."""
import unittest,sys,json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import price_response as p

class PriceResponseTests(unittest.TestCase):
    def test_price_transforms_are_coherent(self):
        d=pd.DataFrame({'last_observed_price':[100.],'units_lag_1':[7.],'category':['c']})
        v=p.scenario(d,[110.])
        self.assertAlmostEqual(v.price_ratio_to_last_observed.iloc[0],1.1)
        self.assertAlmostEqual(v.price_change_pct.iloc[0],10.)
        self.assertAlmostEqual(v.log_price_ratio.iloc[0],np.log(1.1))
        self.assertEqual(v.units_lag_1.iloc[0],7.)
        self.assertEqual(v.category.iloc[0],'c')
    def test_old_experiment_is_unchanged(self):
        before=json.loads((p.A/'preserved_before.json').read_text())
        self.assertEqual(before,p.protected_files())
        old=joblib.load(ROOT/'artifacts/product/chosen_model.joblib')
        self.assertEqual(old['name'],'MovingAverage4')
    def test_only_price_is_contemporaneous(self):
        forbidden=['target_units','label_available_train','label_available_selection','price_eventual','price_train','price_selection','no_recorded_sale','scenario_week_orders','scenario_week_sellers']
        self.assertTrue(set(forbidden).isdisjoint(p.FEATURES))
        self.assertEqual([c for c in p.NUM if c not in p.HIST],['log_last_observed_price','log_price_ratio'])
        frame=pd.read_csv(p.D/'active_product_week.csv',parse_dates=['week','max_source_purchase','max_source_available'])
        for col in ['max_source_purchase','max_source_available']:
            self.assertTrue((frame[col].isna()|frame[col].lt(frame.week)).all())
        self.assertTrue((frame.target_units>0).all())
    def test_saved_predictive_artifact_reproduces_predictions(self):
        b=joblib.load(p.A/'predictive_candidate.joblib')
        cases=pd.read_csv(p.D/'active_product_week.csv');cases=cases[cases.split=='test']
        raw=p.predict(b['estimator'],cases,b['name'])
        expected=pd.read_csv(p.A/'predictions.csv')
        expected=expected[(expected.model==b['name'])&(expected.split=='test')]
        np.testing.assert_allclose(np.maximum(raw,0),expected.prediction,rtol=1e-7,atol=1e-8)
    def test_scenario_does_not_mutate_history(self):
        cases=pd.read_csv(p.D/'active_product_week.csv').head(10)
        old=cases.copy(deep=True)
        altered=p.scenario(cases,cases.scenario_price*.9)
        pd.testing.assert_frame_equal(cases,old)
        pd.testing.assert_frame_equal(cases[p.HIST+p.CAT],altered[p.HIST+p.CAT])

if __name__=='__main__':unittest.main()
