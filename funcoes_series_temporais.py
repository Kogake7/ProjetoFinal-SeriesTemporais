"""Funções reutilizáveis para análise e modelagem de séries temporais."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL


def _validar_dataframe_features(X: pd.DataFrame) -> None:
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X_avaliacao deve ser um DataFrame com nomes de features")
    if X.empty or X.shape[1] == 0:
        raise ValueError("X_avaliacao não pode estar vazio")
    if not X.columns.is_unique:
        raise ValueError("X_avaliacao deve ter nomes de features únicos")


def calcular_importancia_features(
    modelo: Any,
    X_avaliacao: pd.DataFrame,
    y_avaliacao: Optional[Any] = None,
    *,
    metodo: str = "auto",
    n_repeticoes: int = 10,
    seed: int = 42,
    n_jobs: Optional[int] = None,
    max_amostras: Optional[int] = 3000,
    scoring: str = "neg_mean_absolute_error",
) -> pd.DataFrame:
    """Calcula importância de features para regressores e SARIMAX.

    Para modelos compatíveis com scikit-learn, usa importância por permutação
    sobre o conjunto recebido (normalmente o teste final). Para resultados
    ajustados do statsmodels/SARIMAX, retorna os coeficientes das variáveis
    exógenas e seus p-valores. A coluna ``importancia`` é o aumento médio da
    métrica de erro no primeiro caso e o módulo do coeficiente no segundo.

    ``metodo='auto'`` identifica resultados do statsmodels pela presença de
    ``params``, ``pvalues`` e ``model.exog_names``. Também é possível informar
    explicitamente ``'permutacao'`` ou ``'coeficientes'``.
    """
    _validar_dataframe_features(X_avaliacao)

    metodos_validos = {"auto", "permutacao", "coeficientes"}
    if metodo not in metodos_validos:
        raise ValueError(f"metodo deve ser um de {sorted(metodos_validos)}")

    eh_resultado_statsmodels = all(
        hasattr(modelo, atributo) for atributo in ("params", "pvalues", "model")
    ) and hasattr(modelo.model, "exog_names")
    if metodo == "auto":
        metodo = "coeficientes" if eh_resultado_statsmodels else "permutacao"

    if metodo == "permutacao":
        if y_avaliacao is None:
            raise ValueError("y_avaliacao é obrigatório para permutation importance")
        if n_repeticoes < 1:
            raise ValueError("n_repeticoes deve ser maior ou igual a 1")
        if max_amostras is not None and max_amostras < 1:
            raise ValueError("max_amostras deve ser positivo ou None")

        y_serie = pd.Series(y_avaliacao)
        if len(X_avaliacao) != len(y_serie):
            raise ValueError("X_avaliacao e y_avaliacao devem ter o mesmo tamanho")
        if isinstance(y_avaliacao, pd.Series) and not X_avaliacao.index.equals(
            y_avaliacao.index
        ):
            raise ValueError("Os índices de X_avaliacao e y_avaliacao devem coincidir")

        if max_amostras is not None and len(X_avaliacao) > max_amostras:
            posicoes = (
                pd.Series(np.arange(len(X_avaliacao)))
                .sample(n=max_amostras, random_state=seed)
                .sort_values()
                .to_numpy()
            )
            X_usado = X_avaliacao.iloc[posicoes]
            y_usado = y_serie.iloc[posicoes]
        else:
            X_usado = X_avaliacao
            y_usado = y_serie

        resultado = permutation_importance(
            modelo,
            X_usado,
            y_usado,
            scoring=scoring,
            n_repeats=n_repeticoes,
            random_state=seed,
            n_jobs=n_jobs,
        )
        tabela = pd.DataFrame(
            {
                "feature": X_avaliacao.columns,
                "importancia": resultado.importances_mean,
                "desvio_importancia": resultado.importances_std,
                "metodo": "permutacao",
                "coeficiente": np.nan,
                "p_valor": np.nan,
            }
        )
        tabela.attrs["n_amostras"] = len(X_usado)
        tabela.attrs["scoring"] = scoring
    else:
        if not eh_resultado_statsmodels:
            raise TypeError(
                "O método 'coeficientes' requer um resultado ajustado do statsmodels"
            )
        nomes_exogenas = list(modelo.model.exog_names or [])
        if len(nomes_exogenas) != X_avaliacao.shape[1]:
            raise ValueError(
                "A quantidade de features difere das exógenas usadas no SARIMAX"
            )

        nomes_parametros = list(modelo.param_names)
        parametros = pd.Series(np.asarray(modelo.params), index=nomes_parametros)
        p_valores = pd.Series(np.asarray(modelo.pvalues), index=nomes_parametros)
        coeficientes = np.asarray(
            [parametros.get(nome, np.nan) for nome in nomes_exogenas], dtype=float
        )
        tabela = pd.DataFrame(
            {
                "feature": X_avaliacao.columns,
                "importancia": np.abs(coeficientes),
                "desvio_importancia": np.nan,
                "metodo": "coeficiente_sarimax",
                "coeficiente": coeficientes,
                "p_valor": [p_valores.get(nome, np.nan) for nome in nomes_exogenas],
            }
        )

    return tabela.sort_values("importancia", ascending=False).reset_index(drop=True)


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


__all__ = [
    "analisar_componente_residual",
    "calcular_forca_sazonalidade",
    "calcular_importancia_features",
]
