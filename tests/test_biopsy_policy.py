import unittest
import pandas as pd
from biopsy_policy import select_biopsies, patient_expression

class BiopsyPolicyTests(unittest.TestCase):
    def labels(self):
        return pd.DataFrame({'sample_id':['a1','a2','b1','b2','c1'], 'dataset_id':['G']*5,
            'patient_id':['a','a','b','b','c'], 'biopsy_number':[1,2,1,2,1],
            'fibrosis_stage':[1,1,1,3,4]})
    def test_same_stage_averaged_and_changed_stage_first(self):
        labels=self.labels();expr=pd.DataFrame({'sample_id':labels.sample_id,
            'ensembl_id':['gene']*5,'value_z':[2.,4.,10.,100.,8.]})
        result=patient_expression(expr,labels).set_index('patient_id')
        self.assertEqual(result.value_z.to_dict(),{'a':3.,'b':10.,'c':8.})
        self.assertEqual(result.fibrosis_stage.to_dict(),{'a':1,'b':1,'c':4})
    def test_selection_independent_of_input_order(self):
        self.assertEqual(set(select_biopsies(self.labels().iloc[::-1]).sample_id),{'a1','a2','b1','c1'})
    def test_second_cannot_reenter_later_contrast(self):
        selected=select_biopsies(self.labels())
        self.assertNotIn('b2',set(selected[selected.fibrosis_stage.isin([3,4])].sample_id))
    def test_missing_biopsy_order_fails_for_changed_stage(self):
        labels=self.labels();labels.loc[labels.patient_id=='b','biopsy_number']=0
        with self.assertRaises(ValueError):select_biopsies(labels)
    def test_unknown_stages_not_averaged(self):
        labels=self.labels();labels.loc[labels.patient_id=='a','fibrosis_stage']=float('nan')
        self.assertEqual(set(select_biopsies(labels).sample_id),{'a1','b1','c1'})
if __name__=='__main__':unittest.main()
