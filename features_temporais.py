"""T06: atributos causais reutilizáveis para Random Forest e MLP.

Cada linha representa o período a prever. Medições do período corrente nunca
entram nas features: lags e janelas usam somente períodos anteriores. Crie as
features sobre a grade completa, antes de remover linhas incompletas e antes do
corte cronológico. Escala, imputação estatística e encoding aprendido pertencem
ao treino de cada janela (T07/T08), não a este módulo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ConfiguracaoFeatures:
    lags_alvo: tuple[int, ...]
    lags_exogenas: Mapping[str, tuple[int, ...]]
    janelas_moveis: tuple[int, ...]
    calendario: tuple[str, ...]
    indicadores_conhecidos: Mapping[str, str]
    horizonte: int = 1


def configuracao_features(nome: str) -> ConfiguracaoFeatures:
    """Configurações iniciais por base; ajustes de lags são feitos só no treino.

    As exógenas listadas são medidas realizadas, por isso entram defasadas.
    ``holiday`` é a única informação do próprio período: já é conhecida pelo
    calendário antes da previsão. Categorias meteorológicas e direção cardinal
    ficam de fora até haver encoding ajustado dentro de cada janela de treino.
    """
    comum_horario = ('hora', 'dia_semana', 'dia_ano')
    configs = {
        'bitcoin': ConfiguracaoFeatures(
            (1, 2, 3, 7, 14, 28),
            {c: (1, 7) for c in ('priceOpen', 'priceHigh', 'priceLow', 'volume')},
            (7, 14, 28), ('dia_semana', 'dia_ano'), {}),
        'trafego': ConfiguracaoFeatures(
            (1, 2, 3, 24, 48, 168),
            {c: (1, 24) for c in ('temp', 'rain_1h', 'snow_1h', 'clouds_all')},
            (6, 24, 168), comum_horario, {'holiday': 'No Holiday'}),
        'poluicao': ConfiguracaoFeatures(
            (1, 2, 3, 6, 12, 24, 48, 168),
            {c: (1, 24) for c in ('PM10', 'SO2', 'NO2', 'CO', 'O3',
                                   'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM')},
            (6, 24, 168), comum_horario, {}),
        'clima': ConfiguracaoFeatures(
            (1, 2, 3, 6, 12, 24, 48, 168),
            {c: (1, 24) for c in ('p (mbar)', 'rh (%)', 'wv (m/s)',
                                   'wd_sin', 'wd_cos')},
            (6, 24, 168), comum_horario, {}),
        'ouro': ConfiguracaoFeatures(
            (1, 2, 3, 4, 8, 13, 26), {}, (4, 8, 13, 26),
            ('dia_ano',), {}),
    }
    try:
        return configs[nome]
    except KeyError as exc:
        raise ValueError(f'Base desconhecida: {nome!r}') from exc


def _inteiros_positivos(valores: Sequence[int], nome: str, minimo: int) -> list[int]:
    valores = list(valores)
    if not valores or any(isinstance(v, (bool, np.bool_)) or
                          not isinstance(v, (int, np.integer)) or v < minimo
                          for v in valores):
        raise ValueError(f'{nome} deve conter inteiros >= {minimo}.')
    return sorted(set(valores))


def construir_features_temporais(
    dados: pd.DataFrame,
    alvo: str,
    *,
    lags_alvo: Sequence[int],
    lags_exogenas: Mapping[str, Sequence[int]],
    janelas_moveis: Sequence[int],
    calendario: Sequence[str] = ('hora', 'dia_semana', 'dia_ano'),
    indicadores_conhecidos: Mapping[str, str] | None = None,
    horizonte: int = 1,
    frequencia: str | None = None,
    remover_incompletos: bool = False,
) -> pd.DataFrame:
    """Retorna ``target`` e features na grade original, sem olhar o futuro.

    ``remover_incompletos=False`` preserva NaN e todas as datas. Para modelar,
    use ``True`` ou ``dropna()`` depois desta função; então aplique o corte de
    treino/teste com a data registrada nos metadados da base tratada.
    """
    if not isinstance(dados, pd.DataFrame) or not isinstance(dados.index, pd.DatetimeIndex):
        raise TypeError('dados deve ser DataFrame com DatetimeIndex.')
    if dados.empty or dados.index.hasnans or not dados.index.is_unique or not dados.index.is_monotonic_increasing:
        raise ValueError('Índice temporal deve ser não vazio, válido, único e crescente.')
    if frequencia is not None:
        esperado = pd.date_range(dados.index.min(), dados.index.max(), freq=frequencia,
                                 tz=dados.index.tz, name=dados.index.name)
        if not dados.index.equals(esperado):
            raise ValueError('A grade temporal tem lacunas; preserve-as como linhas com NaN.')
    if alvo not in dados or alvo == 'target':
        raise ValueError('Coluna alvo inexistente ou nome reservado target.')
    if isinstance(horizonte, bool) or not isinstance(horizonte, (int, np.integer)) or horizonte < 1:
        raise ValueError('horizonte deve ser inteiro positivo.')
    la = _inteiros_positivos(lags_alvo, 'lags_alvo', horizonte)
    jm = _inteiros_positivos(janelas_moveis, 'janelas_moveis', 2)
    exog = dict(lags_exogenas)
    conhecidos = dict(indicadores_conhecidos or {})
    usadas = set(exog) | set(conhecidos)
    if alvo in usadas or set(exog) & set(conhecidos):
        raise ValueError('Alvo e exógenas conhecidas não podem ter papéis conflitantes.')
    ausentes = usadas - set(dados.columns)
    if ausentes:
        raise ValueError(f'Colunas exógenas ausentes: {sorted(ausentes)}')
    if not pd.api.types.is_numeric_dtype(dados[alvo]):
        raise TypeError('O alvo deve ser numérico.')

    features = pd.DataFrame(index=dados.index)
    for lag in la:
        features[f'target_lag_{lag}'] = dados[alvo].shift(lag)
    for coluna, lags in exog.items():
        if not pd.api.types.is_numeric_dtype(dados[coluna]):
            raise TypeError(f'Exógena {coluna!r} deve ser numérica; faça encoding no treino.')
        for lag in _inteiros_positivos(lags, f'lags de {coluna}', horizonte):
            features[f'{coluna}_lag_{lag}'] = dados[coluna].shift(lag)
    passado = dados[alvo].shift(horizonte)
    for janela in jm:
        features[f'target_roll_mean_{janela}'] = passado.rolling(janela).mean()
        features[f'target_roll_std_{janela}'] = passado.rolling(janela).std()

    componentes = {
        'hora': (dados.index.hour, 24),
        'dia_semana': (dados.index.dayofweek, 7),
        'dia_ano': (dados.index.dayofyear, 365.25),
    }
    for item in calendario:
        if item not in componentes:
            raise ValueError(f'Componente de calendário desconhecido: {item!r}')
        valores, periodo = componentes[item]
        features[f'{item}_sin'] = np.sin(2 * np.pi * valores / periodo)
        features[f'{item}_cos'] = np.cos(2 * np.pi * valores / periodo)
    for coluna, referencia in conhecidos.items():
        serie = dados[coluna]
        features[f'{coluna}_indicador'] = (serie.ne(referencia).astype(float)
                                          .where(serie.notna()))
    if features.columns.has_duplicates:
        raise ValueError('Nomes de features duplicados.')
    resultado = pd.concat([dados[alvo].rename('target'), features], axis=1)
    return resultado.dropna() if remover_incompletos else resultado


def preparar_features_base(dados: pd.DataFrame, nome: str, alvo: str,
                          frequencia: str, *, remover_incompletos: bool = False
                          ) -> pd.DataFrame:
    """Atalho para aplicar a configuração inicial T06 de uma das cinco bases."""
    cfg = configuracao_features(nome)
    return construir_features_temporais(
        dados, alvo, lags_alvo=cfg.lags_alvo,
        lags_exogenas=cfg.lags_exogenas,
        janelas_moveis=cfg.janelas_moveis, calendario=cfg.calendario,
        indicadores_conhecidos=cfg.indicadores_conhecidos,
        horizonte=cfg.horizonte, frequencia=frequencia,
        remover_incompletos=remover_incompletos,
    )
