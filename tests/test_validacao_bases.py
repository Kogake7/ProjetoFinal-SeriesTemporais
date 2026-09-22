import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from validacao_bases import (
    CONFIGURACOES,
    ConfiguracaoBase,
    calcular_sha256,
    validar_dataframe,
    verificar_congelamento,
)


class TestValidacaoBases(unittest.TestCase):
    def setUp(self):
        self.config = ConfiguracaoBase(
            nome="teste",
            caminho="teste.csv",
            coluna_data="data",
            frequencia="D",
        )

    def test_aprova_serie_diaria_regular(self):
        dados = pd.DataFrame(
            {
                "data": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "valor": [10.0, 11.0, 12.0],
            }
        )

        relatorio = validar_dataframe(dados, self.config)

        self.assertTrue(relatorio.aprovada)
        self.assertTrue(relatorio.frequencia_regular)
        self.assertEqual(relatorio.timestamps_ausentes, 0)

    def test_granularidades_de_modelagem_dos_grupos_4_e_5(self):
        self.assertEqual(CONFIGURACOES["clima"].frequencia_modelagem, "h")
        self.assertEqual(CONFIGURACOES["ouro"].frequencia_modelagem, "W-FRI")

    def test_detecta_nulo_duplicata_data_invalida_e_lacuna(self):
        dados = pd.DataFrame(
            {
                "data": [
                    "2024-01-01",
                    "2024-01-01",
                    "2024-01-03",
                    "data-invalida",
                ],
                "valor": [10.0, 10.0, None, 13.0],
            }
        )

        relatorio = validar_dataframe(dados, self.config)

        self.assertFalse(relatorio.aprovada)
        self.assertEqual(relatorio.nulos_por_coluna, {"valor": 1})
        self.assertEqual(relatorio.duplicatas_exatas, 1)
        self.assertEqual(relatorio.datas_invalidas, 1)
        self.assertEqual(relatorio.datas_duplicadas, 1)
        self.assertEqual(relatorio.timestamps_ausentes, 1)

    def test_verificacao_detecta_snapshot_alterado(self):
        with tempfile.TemporaryDirectory() as temporario:
            diretorio = Path(temporario)
            arquivo = diretorio / "grupo" / "base.csv"
            arquivo.parent.mkdir()
            arquivo.write_text("data,valor\n2024-01-01,1\n", encoding="utf-8")
            manifesto = {
                "versao": 1,
                "arquivos": [
                    {
                        "base": "teste",
                        "arquivo": "grupo/base.csv",
                        "tamanho_bytes": arquivo.stat().st_size,
                        "sha256": calcular_sha256(arquivo),
                    }
                ],
            }
            (diretorio / "manifesto.json").write_text(
                json.dumps(manifesto), encoding="utf-8"
            )

            self.assertTrue(verificar_congelamento(diretorio)["integro"])
            arquivo.write_text("conteúdo alterado", encoding="utf-8")
            self.assertFalse(verificar_congelamento(diretorio)["integro"])


if __name__ == "__main__":
    unittest.main()
