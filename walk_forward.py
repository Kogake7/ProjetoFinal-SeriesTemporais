"""T08: corte, horizonte e origens de avaliação comuns por base.

Regra única para as cinco bases:

- corte cronológico vindo de ``dados_tratados`` (``inicio_teste`` dos metadados);
- horizonte de 1 passo (dia, hora ou semana, conforme a base);
- origens de teste = timestamps do teste com alvo e features completos,
  segundo ``preparar_features_base``; cada modelo deve usar essas datas;
- features só com informação até ``t-1``; escalonadores e hiperparâmetros
  ajustados apenas no histórico.

Uso em um modelo novo::

    from walk_forward import dividir_treino_teste
    treino, teste = dividir_treino_teste("bitcoin")

Uso para conferir previsões já salvas::

    from walk_forward import validar_previsoes
    validar_previsoes("clima", previsoes["data"])
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from features_temporais import preparar_features_base
from preparacao_bases import RAIZ_PROJETO, carregar_base_tratada

HORIZONTE = 1
BASES = ("bitcoin", "trafego", "poluicao", "clima", "ouro")

# Política de treino declarada por modelo (texto do protocolo).
POLITICAS = {
    "random_forest": "modelo fixo ajustado no treino; entradas atualizadas a cada passo",
    "mlp": "modelo fixo ajustado no treino; entradas atualizadas a cada passo",
    "sarimax": "reajuste periódico em janela deslizante; estado atualizado a cada passo",
    "holt_winters": "a definir pelo responsável, respeitando corte e horizonte",
}


@lru_cache(maxsize=None)
def _matriz(base: str, raiz: str) -> tuple[pd.DataFrame, dict]:
    df, meta = carregar_base_tratada(base, raiz)
    dados = preparar_features_base(
        df, base, meta["alvo"], meta["frequencia"], remover_incompletos=True
    )
    return dados, meta


def protocolo(base: str, raiz: str | Path = RAIZ_PROJETO) -> dict:
    """Resumo do protocolo da base: corte, horizonte e número de origens."""
    dados, meta = _matriz(base, str(raiz))
    inicio = pd.Timestamp(meta["inicio_teste"])
    origens = dados.index[dados.index >= inicio]
    return {
        "base": base,
        "alvo": meta["alvo"],
        "frequencia": meta["frequencia"],
        "treino": meta["treino"],
        "seed": meta["seed"],
        "inicio_teste": inicio,
        "horizonte": HORIZONTE,
        "n_treino": int((dados.index < inicio).sum()),
        "n_origens": len(origens),
        "n_grade_teste": meta["linhas_teste"],
        "cobertura_grade_pct": 100 * len(origens) / meta["linhas_teste"],
        "primeira_origem": origens.min(),
        "ultima_origem": origens.max(),
    }


def dividir_treino_teste(
    base: str, raiz: str | Path = RAIZ_PROJETO
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Matriz causal (coluna ``target`` + features) dividida no corte oficial."""
    dados, meta = _matriz(base, str(raiz))
    inicio = pd.Timestamp(meta["inicio_teste"])
    treino = dados.loc[dados.index < inicio]
    teste = dados.loc[dados.index >= inicio]
    if treino.empty or teste.empty or treino.index.max() >= teste.index.min():
        raise ValueError(f"{base}: divisão temporal inválida.")
    return treino.copy(), teste.copy()


def origens_teste(base: str, raiz: str | Path = RAIZ_PROJETO) -> pd.DatetimeIndex:
    """Datas oficiais de teste (uma previsão de 1 passo por data)."""
    return pd.DatetimeIndex(dividir_treino_teste(base, raiz)[1].index, name="data")


def validar_previsoes(
    base: str, datas_previstas, raiz: str | Path = RAIZ_PROJETO
) -> dict:
    """Confere se um modelo previu exatamente as origens oficiais da base."""
    oficiais = origens_teste(base, raiz)
    previstas = pd.DatetimeIndex(pd.to_datetime(datas_previstas))
    resultado = {
        "base": base,
        "origens_oficiais": len(oficiais),
        "previsoes": len(previstas),
        "duplicadas": int(previstas.duplicated().sum()),
        "ordenadas": bool(previstas.is_monotonic_increasing),
        "faltando": len(oficiais.difference(previstas)),
        "fora_do_protocolo": len(previstas.difference(oficiais)),
    }
    resultado["ok"] = (
        resultado["duplicadas"] == 0
        and resultado["ordenadas"]
        and resultado["faltando"] == 0
        and resultado["fora_do_protocolo"] == 0
    )
    return resultado


__all__ = [
    "BASES", "HORIZONTE", "POLITICAS", "dividir_treino_teste",
    "origens_teste", "protocolo", "validar_previsoes",
]
