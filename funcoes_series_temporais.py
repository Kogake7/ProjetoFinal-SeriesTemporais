"""Funções reutilizáveis para diagnóstico de sazonalidade e resíduos."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL


def calcular_forca_sazonalidade(serie: pd.Series, periodo: int, robust: bool = True,) -> dict[str, Any]:
    """Calcula a força da sazonalidade e retorna a decomposição STL."""
    serie = pd.Series(serie).dropna().astype(float)
    if periodo < 2:
        raise ValueError("periodo deve ser maior ou igual a 2")
    if len(serie) < 2 * periodo:
        raise ValueError("A série precisa ter pelo menos dois ciclos completos")

    janela = periodo if periodo % 2 else periodo + 1
    decomposicao = STL(
        serie,
        period=periodo,
        seasonal=janela,
        robust=robust,
    ).fit()
    residuo = np.asarray(decomposicao.resid)
    sazonal_com_residuo = np.asarray(decomposicao.seasonal + decomposicao.resid)
    tendencia_com_residuo = np.asarray(decomposicao.trend + decomposicao.resid)

    variancia_residuo = np.var(residuo)
    forca = max(
        0.0,
        1.0 - variancia_residuo / np.var(sazonal_com_residuo),
    )
    forca_tendencia = max(
        0.0,
        1.0 - variancia_residuo / np.var(tendencia_com_residuo),
    )

    return {
        "periodo": periodo,
        "forca_sazonalidade": float(forca),
        "forca_tendencia": float(forca_tendencia),
        "decomposicao": decomposicao,
    }


def analisar_componente_residual(
    decomposicao: Any,
    lags: int = 24,
) -> dict[str, Any]:
    """Resume o componente residual da decomposição e testa autocorrelação."""
    residuo = pd.Series(decomposicao.resid).dropna().astype(float)
    lags_validos = max(1, min(lags, len(residuo) // 5))
    ljung_box = acorr_ljungbox(residuo, lags=lags_validos, return_df=True)

    return {
        "media": float(residuo.mean()),
        "desvio_padrao": float(residuo.std()),
        "assimetria": float(residuo.skew()),
        "autocorrelacao_residual": ljung_box,
        "residuo": residuo,
    }


__all__ = ["analisar_componente_residual", "calcular_forca_sazonalidade"]
