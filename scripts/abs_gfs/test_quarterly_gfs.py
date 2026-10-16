"""Integration checks against the downloaded source; no source files are edited."""
import unittest
from unittest.mock import patch
import openpyxl
import quarterly_gfs as gfs

RAW=gfs.ROOT/'data/abs_gfs/raw/quarterly/jun-2026'

class QuarterlyTests(unittest.TestCase):
    def calculate(self): return gfs.calculate(RAW/'quarterly.xlsx',RAW/'insights.html')
    def test_published_reconciliation(self):
        result,rows=self.calculate()
        self.assertEqual(result['totals_millions']['revenue'],1073387)
        self.assertEqual(result['totals_millions']['expenses'],1111169)
        self.assertEqual(result['totals_millions']['net_operating_balance'],-37783)
        self.assertEqual(result['previous_taxation_millions'],833919)
        self.assertEqual(result['rounding_identity_difference_millions'],1)
        self.assertTrue(all(c['status']=='PASS' for c in result['checks']))
        self.assertEqual(len(rows),20)
    def assert_rejected(self,cell,value,regex):
        book=openpyxl.load_workbook(RAW/'quarterly.xlsx',data_only=True)
        book['Table 1'][cell]=value
        with patch.object(gfs.openpyxl,'load_workbook',return_value=book):
            with self.assertRaisesRegex(ValueError,regex): self.calculate()
        book.close()
    def test_missing_quarter(self): self.assert_rejected('E6',None,'four quarters')
    def test_wrong_order(self): self.assert_rejected('E6','Jun Qtr 2025','complete July-June')
    def test_suppressed_value(self): self.assert_rejected('B14','np','Non-numeric')
    def test_wrong_units(self): self.assert_rejected('B7','$b','AUD millions')
    def test_wrong_sector(self): self.assert_rejected('A4','Public corporations','sector')
    def test_changed_revenue_fails_validation(self): self.assert_rejected('B14',245852,'identity')
    def test_duplicate_measure(self): self.assert_rejected('A50','Total GFS revenue','exactly one')
    def test_mixed_vintage_tax(self): self.assert_rejected('B9',199529,'do not reconcile')

if __name__=='__main__': unittest.main()
