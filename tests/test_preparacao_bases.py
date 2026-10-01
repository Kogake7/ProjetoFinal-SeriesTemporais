import unittest
import numpy as np
import pandas as pd
from preparacao_bases import PROTOCOLO, tratar_base, validar_tratada


class TestPreparacaoBases(unittest.TestCase):
    def clima(self):
        return pd.DataFrame({
            'Date Time': ['01.01.2020 00:10:00', '01.01.2020 00:20:00',
                          '01.01.2020 01:10:00', '01.01.2020 03:10:00'],
            'T (degC)': [10., 12., 14., 16.], 'wd (deg)': [359., 1., 90., 180.],
            'wv (m/s)': [2., 4., -9999., 2.], 'max. wv (m/s)': [3., 7., -9999., 5.],
        })

    def test_clima_circular_maximo_sentinela_e_grade(self):
        df, meta = tratar_base('clima', self.clima())
        self.assertEqual(df.iloc[0]['max. wv (m/s)'], 7.)
        self.assertLess(min(df.iloc[0]['wd (deg)'], 360-df.iloc[0]['wd (deg)']), 0.01)
        self.assertEqual(df.iloc[1]['wv (m/s)'], 3.)
        self.assertTrue(pd.isna(df.iloc[2]['T (degC)']))
        self.assertEqual(len(df), 4)
        self.assertEqual(meta['linhas_treino'], 3)

    def test_dados_futuros_nao_alteram_passado(self):
        fonte = self.clima()
        original, _ = tratar_base('clima', fonte)
        fonte.loc[3, 'T (degC)'] = 99
        fonte.loc[3, 'wv (m/s)'] = 900
        alterado, _ = tratar_base('clima', fonte)
        pd.testing.assert_frame_equal(original.iloc[:3], alterado.iloc[:3])

    def test_ouro_converte_marcador_e_usa_ultimo_valido(self):
        fonte = pd.DataFrame({'DATE':['2020-01-02','2020-01-03','2020-01-10', '2020-01-17'],
                              'VALUE':['100', '.', '120', '130']})
        df, _ = tratar_base('ouro', fonte)
        self.assertEqual(df.iloc[0]['VALUE'], 100)
        self.assertEqual(df.index[0], pd.Timestamp('2020-01-03'))

    def test_trafego_duplicado_nao_soma_e_conflito_vira_ausencia(self):
        fonte = pd.DataFrame({'date_time':['2020-01-01 00:00', '2020-01-01 00:00',
                                           '2020-01-01 01:00','2020-01-01 01:00', '2020-01-01 02:00'],
            'traffic_volume':[100,100,200,250,300], 'holiday':[None]*5,
            'temp':[280]*5, 'rain_1h':[0]*5, 'snow_1h':[0]*5,
            'weather_main':['Clouds','Rain','Clouds','Rain','Clouds']})
        df, meta = tratar_base('trafego', fonte)
        self.assertEqual(df.iloc[0]['traffic_volume'],100)
        self.assertTrue(pd.isna(df.iloc[1]['traffic_volume']))
        self.assertEqual(meta['diagnostico']['timestamps_com_alvos_conflitantes'],1)
        self.assertEqual(df.iloc[0]['holiday'],'No Holiday')

    def test_exogenas_nao_preenchem_lacuna_longa(self):
        fonte = self.clima()
        fonte.loc[3,'Date Time'] = '02.01.2020 03:10:00'
        df, _ = tratar_base('clima', fonte)
        self.assertTrue(pd.isna(df.loc['2020-01-01 12:00','wv (m/s)']))
        self.assertTrue(pd.isna(df.loc['2020-01-01 12:00','T (degC)']))

    def test_configuracoes_oficiais(self):
        self.assertEqual([p['seed'] for p in PROTOCOLO.values()],[42,67,42,42,42])
        self.assertEqual([p['treino'] for p in PROTOCOLO.values()],[.7,.8,.8,.8,.75])

    def test_rejeita_grade_irregular(self):
        df = pd.DataFrame({'VALUE':[1.,2.]},index=pd.to_datetime(['2020-01-03','2020-01-17']))
        with self.assertRaises(ValueError):
            validar_tratada(df,'ouro')


if __name__ == '__main__':
    unittest.main()
