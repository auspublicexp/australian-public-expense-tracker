"""Guard against a second top-level generation pass in the IPEA scripts."""
import ast
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent


class GeneratorEntrypointTests(unittest.TestCase):
    def test_search_defaults_to_generated_outputs_without_a_website(self):
        with patch.dict(os.environ, {}, clear=True):
            index = runpy.run_path(str(SCRIPTS / 'build_ipea_search_index.py'))
        output = SCRIPTS.parents[1] / 'output' / 'ipea'
        self.assertEqual(index['CHART_ROOT'], output)
        self.assertEqual(index['INDEX_PATH'], output / 'ipea-search-index.json')

    def test_search_honours_explicit_website_paths(self):
        with patch.dict(os.environ, {'APET_IPEA_CHART_ROOT': 'site/charts', 'APET_IPEA_SEARCH_INDEX': 'site/index.json'}, clear=True):
            index = runpy.run_path(str(SCRIPTS / 'build_ipea_search_index.py'))
        self.assertEqual(index['CHART_ROOT'], Path('site/charts'))
        self.assertEqual(index['INDEX_PATH'], Path('site/index.json'))

    def test_quarterly_generation_runs_once_before_indexing(self):
        self.assert_single_generation_pass('generate_quarterly_charts.py', 'generate_quarter')

    def test_annual_generation_runs_once_before_indexing(self):
        self.assert_single_generation_pass('generate_annual_charts.py', 'generate_financial_year')

    def assert_single_generation_pass(self, filename, generator):
        body = ast.parse((SCRIPTS / filename).read_text(encoding='utf-8-sig')).body
        calls = [
            (node.lineno, node.func.id)
            for statement in body if not isinstance(statement, (ast.FunctionDef, ast.ClassDef))
            for node in ast.walk(statement)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in (generator, 'build_ipea_search_index')
        ]
        self.assertEqual([name for _, name in sorted(calls)], [generator, 'build_ipea_search_index'])


if __name__ == '__main__':
    unittest.main()
