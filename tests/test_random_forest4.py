"""Verifica as funções efetivamente utilizadas no notebook, sem treinar florestas."""
import ast
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from features_temporais import construir_features_temporais


class TestFeaturesRandomForest4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook = json.loads((Path(__file__).resolve().parents[1] /
                               'grupo4/random-forest-4.ipynb').read_text(encoding='utf-8'))
        scope = {'pd': pd, 'np': np, 'HORIZON': 1}
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code':
                continue
            tree = ast.parse(''.join(cell['source']))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in {
                    'construir_features_temporais', 'maior_trecho_continuo'
                }:
                    exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook>', 'exec'), scope)
        cls.criar = staticmethod(construir_features_temporais)
        cls.trecho = staticmethod(scope['maior_trecho_continuo'])

    def fonte(self):
        return pd.DataFrame({'y': np.arange(400, dtype=float), 'x': np.arange(400, dtype=float) * 2},
                            index=pd.date_range('2020-01-01', periods=400, freq='h'))

    def test_lacunas_nao_comprimem_lags(self):
        dados = self.fonte()
        dados.iloc[200, 0] = np.nan
        resultado = self.criar(dados, 'y', lags_alvo=[1, 24], lags_exogenas={},
                              janelas_moveis=[], frequencia='h', remover_incompletos=True)
        self.assertNotIn(dados.index[201], resultado.index)
        self.assertNotIn(dados.index[224], resultado.index)
        self.assertEqual(resultado.loc[dados.index[202], 'target_lag_1'], 201.)
        self.assertEqual(resultado.loc[dados.index[202], 'target_lag_24'], 178.)

    def test_futuro_nao_altera_features_da_origem(self):
        dados = self.fonte()
        kwargs = dict(lags_alvo=[1, 24], lags_exogenas={'x': [1]}, janelas_moveis=[6, 24],
                      frequencia='h', remover_incompletos=True)
        original = self.criar(dados, 'y', **kwargs)
        dados.iloc[250:] = 99999.
        alterado = self.criar(dados, 'y', **kwargs)
        pd.testing.assert_frame_equal(original.drop(columns='target').loc[:dados.index[250]],
                                      alterado.drop(columns='target').loc[:dados.index[250]])

    def test_diagnostico_escolhe_segmento_continuo(self):
        dados = self.fonte()['y']
        dados.iloc[100] = np.nan
        trecho = self.trecho(dados)
        self.assertEqual(trecho.index[0], dados.index[101])
        self.assertEqual(len(trecho), 299)
        self.assertTrue(trecho.notna().all())


if __name__ == '__main__':
    unittest.main()
