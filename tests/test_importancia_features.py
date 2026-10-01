import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from funcoes_series_temporais import calcular_importancia_features


def test_importancia_permutacao_tem_saida_padronizada_e_amostragem():
    rng = np.random.default_rng(42)
    X = pd.DataFrame(rng.normal(size=(80, 2)), columns=["forte", "ruido"])
    y = pd.Series(5 * X["forte"] + rng.normal(scale=0.01, size=len(X)))
    modelo = RandomForestRegressor(n_estimators=30, random_state=42).fit(X, y)

    resultado = calcular_importancia_features(
        modelo, X, y, n_repeticoes=3, seed=42, max_amostras=40
    )

    assert list(resultado.columns) == [
        "feature",
        "importancia",
        "desvio_importancia",
        "metodo",
        "coeficiente",
        "p_valor",
    ]
    assert resultado.loc[0, "feature"] == "forte"
    assert resultado.attrs["n_amostras"] == 40
    assert set(resultado["metodo"]) == {"permutacao"}


def test_importancia_permutacao_rejeita_indices_desalinhados():
    X = pd.DataFrame({"x": [1.0, 2.0]}, index=[10, 11])
    y = pd.Series([1.0, 2.0], index=[11, 12])

    with pytest.raises(ValueError, match="índices"):
        calcular_importancia_features(object(), X, y)


class _ModeloStatsmodelsFalso:
    exog_names = ["x1", "x2"]


class _ResultadoStatsmodelsFalso:
    model = _ModeloStatsmodelsFalso()
    param_names = ["intercept", "x1", "x2", "ar.L1", "sigma2"]
    params = np.array([0.1, -0.8, 0.2, 0.4, 1.0])
    pvalues = np.array([0.5, 0.01, 0.2, 0.1, 0.0])


def test_importancia_sarimax_considera_apenas_exogenas():
    X = pd.DataFrame(columns=["temperatura_lag1", "pressao"])
    # A função exige ao menos uma linha, mas usa X apenas para nomear as exógenas.
    X.loc[0] = [0.0, 0.0]

    resultado = calcular_importancia_features(
        _ResultadoStatsmodelsFalso(), X, metodo="coeficientes"
    )

    assert resultado["feature"].tolist() == ["temperatura_lag1", "pressao"]
    assert resultado["coeficiente"].tolist() == [-0.8, 0.2]
    assert resultado["importancia"].tolist() == [0.8, 0.2]
    assert set(resultado["metodo"]) == {"coeficiente_sarimax"}
