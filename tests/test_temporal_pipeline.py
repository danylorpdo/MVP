"""Regressões contra vazamento temporal e semântica de semanas sem transação."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import modeling as m

class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.weeks=m.WEEKS
        m.WEEKS=pd.date_range('2017-01-02','2017-02-06',freq='7D')
        self.x=pd.DataFrame([
            {'product_id':'p','category':'c','order_id':'a','seller_id':'s','purchase':pd.Timestamp('2017-01-03'),'available':pd.Timestamp('2017-01-05'),'week':pd.Timestamp('2017-01-02'),'order_status':'delivered','price':10.,'price_cents':1000,'freight_value':2.},
            {'product_id':'p','category':'c','order_id':'b','seller_id':'s','purchase':pd.Timestamp('2017-01-17'),'available':pd.Timestamp('2017-02-10'),'week':pd.Timestamp('2017-01-16'),'order_status':'delivered','price':99.,'price_cents':9900,'freight_value':2.},
        ])
    def tearDown(self):m.WEEKS=self.weeks
    def panel(self,x):return m.make_panel(x,['p'],{'p':'c'},'product')
    def test_future_purchase_and_delivery_cannot_change_past_features(self):
        before=self.panel(self.x)
        future=self.x.iloc[[0]].copy();future['purchase']=pd.Timestamp('2017-02-07');future['available']=pd.Timestamp('2017-02-08');future['week']=pd.Timestamp('2017-02-06');future['price']=9999.
        after=self.panel(pd.concat([self.x,future],ignore_index=True))
        pd.testing.assert_frame_equal(before[m.FEATURES],after[m.FEATURES])
        self.assertNotEqual(before.target_units.iloc[-1],after.target_units.iloc[-1])
    def test_old_purchase_with_future_delivery_not_known(self):
        p=self.panel(self.x)
        row=p[p.week.eq('2017-01-23')].iloc[0]
        self.assertEqual(row.units_lag_1,0)
        self.assertEqual(row.last_observed_price,10)
        self.assertEqual(row.max_source_available,pd.Timestamp('2017-01-05'))
    def test_zero_sales_is_not_known_availability(self):
        p=self.panel(self.x)
        row=p[p.week.eq('2017-01-09')].iloc[0]
        self.assertEqual(row.target_units,0)
        self.assertTrue(row.no_recorded_sale)
        self.assertEqual(row.availability_state,'unknown')
        self.assertNotIn('no_recorded_sale',m.FEATURES)
        self.assertNotIn('target_units',m.FEATURES)
    def test_exact_cutoff_not_visible(self):
        x=self.x.copy();x.loc[0,'available']=pd.Timestamp('2017-01-09')
        p=self.panel(x)
        self.assertEqual(p[p.week.eq('2017-01-09')].iloc[0].units_lag_1,0)
    def test_boundary_week_is_excluded(self):
        self.assertEqual(m.split_for(pd.Timestamp('2018-04-30')),'boundary_excluded')
        self.assertEqual(m.split_for(pd.Timestamp('2018-04-23')),'validation')
        self.assertEqual(m.split_for(pd.Timestamp('2018-05-07')),'test')
    def test_label_censoring_is_explicit(self):
        x=self.x.copy();x.loc[0,'available']=pd.Timestamp('2018-02-01')
        p=self.panel(x);row=p.iloc[0]
        self.assertEqual(row.target_units,1)
        self.assertEqual(row.label_available_train,0)

if __name__=='__main__':unittest.main()
