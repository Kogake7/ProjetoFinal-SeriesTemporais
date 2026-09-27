"""Congelamento e validação sanitária das bases do projeto.

O módulo não corrige nem sobrescreve os dados brutos. Ele oferece duas etapas:

1. ``congelar_bases`` copia as cinco fontes para um diretório de snapshot e cria
   um manifesto com hashes SHA-256;
2. ``validar_todas_bases`` verifica nulos, duplicatas, datas e a frequência
   temporal esperada de cada fonte.

Exemplo de uso em um notebook::

    from validacao_bases import congelar_bases, validar_todas_bases

    congelar_bases("dados_congelados/v1")
    relatorios = validar_todas_bases()
    relatorios["bitcoin"].to_dict()
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd


RAIZ_PROJETO = Path(__file__).resolve().parent
NOME_MANIFESTO = "manifesto.json"


@dataclass(frozen=True)
class ConfiguracaoBase:
    """Regras necessárias para carregar e validar uma série temporal."""

    nome: str
    caminho: str
    frequencia: str
    frequencia_modelagem: str | None = None
    coluna_data: str | None = None
    colunas_data: tuple[str, ...] = ()
    formato_data: str | None = None
    unidade_epoch: str | None = None
    separador: str = ","


CONFIGURACOES: dict[str, ConfiguracaoBase] = {
    "bitcoin": ConfiguracaoBase(
        nome="bitcoin",
        caminho="grupo1/bitcoin.xlsx",
        coluna_data="timeOpen",
        unidade_epoch="ms",
        frequencia="D",
        frequencia_modelagem="D",
    ),
    "trafego": ConfiguracaoBase(
        nome="trafego",
        caminho="grupo2/Metro_Interstate_Traffic_Volume.csv",
        coluna_data="date_time",
        frequencia="h",
        frequencia_modelagem="h",
    ),
    "poluicao": ConfiguracaoBase(
        nome="poluicao",
        caminho="grupo3/PRSA_Data_Aotizhongxin_20130301-20170228.csv",
        colunas_data=("year", "month", "day", "hour"),
        frequencia="h",
        frequencia_modelagem="h",
    ),
    "clima": ConfiguracaoBase(
        nome="clima",
        caminho="grupo4/jena_climate_2009_2016.csv",
        coluna_data="Date Time",
        formato_data="%d.%m.%Y %H:%M:%S",
        frequencia="10min",
        frequencia_modelagem="h",
    ),
    "ouro": ConfiguracaoBase(
        nome="ouro",
        caminho="grupo5/gold.daily.prices.csv",
        coluna_data="DATE",
        frequencia="B",
        frequencia_modelagem="W-FRI",
        separador=r"\s+",
    ),
}


@dataclass
class RelatorioValidacao:
    """Resultado serializável da validação de uma base."""

    nome: str
    arquivo: str
    linhas: int
    colunas: int
    nulos_por_coluna: dict[str, int]
    linhas_com_nulos: int
    duplicatas_exatas: int
    datas_invalidas: int
    datas_duplicadas: int
    ordenacao_datas: str
    frequencia_esperada: str
    frequencia_modelagem: str
    frequencia_regular: bool
    timestamps_ausentes: int
    exemplos_timestamps_ausentes: list[str]
    timestamps_fora_da_grade: int
    exemplos_timestamps_fora_da_grade: list[str]
    aprovada: bool

    def to_dict(self) -> dict[str, Any]:
        """Converte o relatório para dicionário (útil para JSON/DataFrame)."""

        return asdict(self)


def _obter_configuracao(nome: str) -> ConfiguracaoBase:
    try:
        return CONFIGURACOES[nome]
    except KeyError as exc:
        opcoes = ", ".join(CONFIGURACOES)
        raise ValueError(f"Base desconhecida: {nome!r}. Opções: {opcoes}.") from exc


def _caminho_da_base(config: ConfiguracaoBase, raiz: str | Path | None) -> Path:
    raiz_resolvida = Path(raiz).resolve() if raiz is not None else RAIZ_PROJETO
    return raiz_resolvida / Path(config.caminho)


def carregar_base(nome: str, raiz: str | Path | None = None) -> pd.DataFrame:
    """Carrega uma das cinco bases sem modificar o arquivo de origem."""

    config = _obter_configuracao(nome)
    caminho = _caminho_da_base(config, raiz)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo da base {nome!r} não encontrado: {caminho}")

    if caminho.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(caminho)
    return pd.read_csv(caminho, sep=config.separador)


def extrair_datas(
    dados: pd.DataFrame, config: ConfiguracaoBase
) -> pd.Series:
    """Extrai a data da base e converte valores inválidos para ``NaT``."""

    if config.colunas_data:
        faltantes = [coluna for coluna in config.colunas_data if coluna not in dados]
        if faltantes:
            raise ValueError(
                f"Colunas de data ausentes em {config.nome!r}: {', '.join(faltantes)}"
            )
        componentes = dados.loc[:, list(config.colunas_data)]
        return pd.to_datetime(componentes, errors="coerce")

    if config.coluna_data is None or config.coluna_data not in dados:
        raise ValueError(
            f"Coluna de data {config.coluna_data!r} ausente em {config.nome!r}."
        )

    valores = dados[config.coluna_data]
    if config.unidade_epoch:
        return pd.to_datetime(
            valores, unit=config.unidade_epoch, errors="coerce", utc=True
        )
    return pd.to_datetime(
        valores, format=config.formato_data, errors="coerce"
    )


def _textos_datas(indice: pd.DatetimeIndex, limite: int = 5) -> list[str]:
    return [data.isoformat() for data in indice[:limite]]


def validar_dataframe(
    dados: pd.DataFrame,
    config: ConfiguracaoBase,
    arquivo: str | Path = "<memória>",
) -> RelatorioValidacao:
    """Valida um DataFrame segundo as regras temporais informadas.

    A regularidade é calculada sobre timestamps únicos. Duplicatas de data são
    reportadas separadamente para não esconder observações repetidas.
    """

    datas = extrair_datas(dados, config)
    datas_validas = datas.dropna()
    datas_unicas = pd.DatetimeIndex(datas_validas.drop_duplicates().sort_values())

    if len(datas_unicas):
        grade_esperada = pd.date_range(
            start=datas_unicas.min(),
            end=datas_unicas.max(),
            freq=config.frequencia,
        )
        ausentes = grade_esperada.difference(datas_unicas)
        fora_da_grade = datas_unicas.difference(grade_esperada)
    else:
        ausentes = pd.DatetimeIndex([])
        fora_da_grade = pd.DatetimeIndex([])

    if datas_validas.empty:
        ordenacao = "sem datas válidas"
    elif datas_validas.is_monotonic_increasing:
        ordenacao = "crescente"
    elif datas_validas.is_monotonic_decreasing:
        ordenacao = "decrescente"
    else:
        ordenacao = "não ordenada"

    nulos = dados.isna().sum()
    nulos_por_coluna = {
        str(coluna): int(total) for coluna, total in nulos.items() if total > 0
    }
    datas_invalidas = int(datas.isna().sum())
    # Conta repetições além da primeira ocorrência, como ``DataFrame.duplicated``.
    datas_duplicadas = int(datas_validas.duplicated().sum())
    duplicatas_exatas = int(dados.duplicated().sum())
    frequencia_regular = (
        len(datas_unicas) > 0
        and datas_invalidas == 0
        and len(ausentes) == 0
        and len(fora_da_grade) == 0
    )
    aprovada = (
        not nulos_por_coluna
        and duplicatas_exatas == 0
        and datas_invalidas == 0
        and datas_duplicadas == 0
        and frequencia_regular
    )

    return RelatorioValidacao(
        nome=config.nome,
        arquivo=str(arquivo),
        linhas=int(dados.shape[0]),
        colunas=int(dados.shape[1]),
        nulos_por_coluna=nulos_por_coluna,
        linhas_com_nulos=int(dados.isna().any(axis=1).sum()),
        duplicatas_exatas=duplicatas_exatas,
        datas_invalidas=datas_invalidas,
        datas_duplicadas=datas_duplicadas,
        ordenacao_datas=ordenacao,
        frequencia_esperada=config.frequencia,
        frequencia_modelagem=config.frequencia_modelagem or config.frequencia,
        frequencia_regular=frequencia_regular,
        timestamps_ausentes=len(ausentes),
        exemplos_timestamps_ausentes=_textos_datas(ausentes),
        timestamps_fora_da_grade=len(fora_da_grade),
        exemplos_timestamps_fora_da_grade=_textos_datas(fora_da_grade),
        aprovada=aprovada,
    )


def validar_base(
    nome: str, raiz: str | Path | None = None
) -> RelatorioValidacao:
    """Carrega e valida uma base cadastrada em ``CONFIGURACOES``."""

    config = _obter_configuracao(nome)
    caminho = _caminho_da_base(config, raiz)
    return validar_dataframe(carregar_base(nome, raiz), config, caminho)


def validar_todas_bases(
    raiz: str | Path | None = None,
) -> dict[str, RelatorioValidacao]:
    """Valida as cinco bases e retorna um relatório por nome."""

    return {nome: validar_base(nome, raiz) for nome in CONFIGURACOES}


def relatorios_como_dataframe(
    relatorios: Mapping[str, RelatorioValidacao],
) -> pd.DataFrame:
    """Cria uma tabela-resumo conveniente para exibição em notebooks."""

    campos = (
        "nome",
        "linhas",
        "colunas",
        "linhas_com_nulos",
        "duplicatas_exatas",
        "datas_invalidas",
        "datas_duplicadas",
        "ordenacao_datas",
        "frequencia_esperada",
        "frequencia_modelagem",
        "frequencia_regular",
        "timestamps_ausentes",
        "timestamps_fora_da_grade",
        "aprovada",
    )
    registros = [relatorio.to_dict() for relatorio in relatorios.values()]
    return pd.DataFrame(registros).loc[:, campos]


def calcular_sha256(caminho: str | Path, tamanho_bloco: int = 1024 * 1024) -> str:
    """Calcula o SHA-256 de um arquivo sem carregá-lo inteiro na memória."""

    digest = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(tamanho_bloco), b""):
            digest.update(bloco)
    return digest.hexdigest()


def congelar_bases(
    destino: str | Path,
    raiz: str | Path | None = None,
) -> Path:
    """Copia as fontes e grava um manifesto que permite detectar alterações.

    Por segurança, ``destino`` deve ser um diretório novo ou vazio. A função
    nunca remove nem sobrescreve snapshots existentes.

    Retorna o caminho do manifesto criado.
    """

    destino = Path(destino).resolve()
    if destino.exists() and not destino.is_dir():
        raise FileExistsError(f"O destino existe e não é um diretório: {destino}")
    if destino.exists() and any(destino.iterdir()):
        raise FileExistsError(
            f"O diretório de congelamento precisa estar vazio: {destino}"
        )

    # Confere todas as origens antes de começar para evitar snapshots parciais.
    origens = {
        nome: _caminho_da_base(config, raiz)
        for nome, config in CONFIGURACOES.items()
    }
    for nome, origem in origens.items():
        if not origem.is_file():
            raise FileNotFoundError(f"Arquivo da base {nome!r} não encontrado: {origem}")

    destino.mkdir(parents=True, exist_ok=True)

    arquivos: list[dict[str, Any]] = []
    for nome, config in CONFIGURACOES.items():
        origem = origens[nome]
        relativo = Path(config.caminho)
        copia = destino / relativo
        copia.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, copia)
        arquivos.append(
            {
                "base": nome,
                "arquivo": relativo.as_posix(),
                "tamanho_bytes": copia.stat().st_size,
                "sha256": calcular_sha256(copia),
            }
        )

    manifesto = {
        "versao": 1,
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "algoritmo_hash": "sha256",
        "arquivos": arquivos,
    }
    caminho_manifesto = destino / NOME_MANIFESTO
    caminho_manifesto.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho_manifesto


def verificar_congelamento(diretorio: str | Path) -> dict[str, Any]:
    """Confere presença, tamanho e hash dos arquivos de um snapshot."""

    diretorio = Path(diretorio).resolve()
    caminho_manifesto = diretorio / NOME_MANIFESTO
    if not caminho_manifesto.is_file():
        raise FileNotFoundError(f"Manifesto não encontrado: {caminho_manifesto}")

    manifesto = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
    resultados: list[dict[str, Any]] = []
    for item in manifesto.get("arquivos", []):
        caminho = diretorio / Path(item["arquivo"])
        existe = caminho.is_file()
        tamanho_confere = existe and caminho.stat().st_size == item["tamanho_bytes"]
        hash_confere = existe and calcular_sha256(caminho) == item["sha256"]
        resultados.append(
            {
                "base": item["base"],
                "arquivo": item["arquivo"],
                "existe": existe,
                "tamanho_confere": tamanho_confere,
                "hash_confere": hash_confere,
                "integro": existe and tamanho_confere and hash_confere,
            }
        )

    return {
        "integro": bool(resultados) and all(item["integro"] for item in resultados),
        "arquivos": resultados,
    }


__all__ = [
    "CONFIGURACOES",
    "ConfiguracaoBase",
    "RelatorioValidacao",
    "calcular_sha256",
    "carregar_base",
    "congelar_bases",
    "extrair_datas",
    "relatorios_como_dataframe",
    "validar_base",
    "validar_dataframe",
    "validar_todas_bases",
    "verificar_congelamento",
]
