# ProjetoFinal-SeriesTemporais

Projeto final de Séries Temporais contendo quatro modelos de previsão:
SARIMAX, Holt-Winters, Random Forest e MLP Regressor (redes neurais), aplicados
a cinco bases diferentes.

## Congelamento e validação das bases

O arquivo `validacao_bases.py` centraliza o carregamento e as verificações de:

- valores nulos;
- linhas e datas duplicadas;
- datas inválidas e ordenação cronológica;
- frequência regular, respeitando a periodicidade própria de cada base.

Uso em notebook ou script:

```python
from validacao_bases import (
    congelar_bases,
    relatorios_como_dataframe,
    validar_todas_bases,
    verificar_congelamento,
)

# Cria uma cópia versionável e um manifesto com hashes SHA-256.
manifesto = congelar_bases("dados_congelados/v1")

# Confere depois se algum arquivo congelado foi alterado.
integridade = verificar_congelamento("dados_congelados/v1")

# Valida diretamente as cinco bases originais.
relatorios = validar_todas_bases()
resumo = relatorios_como_dataframe(relatorios)
display(resumo)
```

O congelamento exige um diretório novo ou vazio e nunca sobrescreve um snapshot
existente. A validação é somente leitura: os dados brutos não são corrigidos ou
alterados automaticamente.

### Notebooks por base

- `grupo1/validacao_sanitaria_bitcoin.ipynb`;
- `grupo2/validacao_sanitaria_trafego.ipynb`;
- `grupo3/validacao_sanitaria_poluicao.ipynb`;
- `grupo4/validacao_sanitaria_clima.ipynb`;
- `grupo5/validacao_sanitaria_ouro.ipynb`.

Cada notebook pode ser aberto a partir da raiz do projeto ou da própria pasta do
grupo. Eles mostram a amostra da base, o relatório consolidado, os nulos por
coluna, exemplos de duplicatas/lacunas e o SHA-256 do arquivo analisado.

As granularidades de modelagem adotadas são: diária para Bitcoin, horária para
tráfego, poluição e clima, e semanal (fechamento na sexta-feira) para ouro. No
caso de clima e ouro, os notebooks mostram também a consolidação dos registros
originais para essas frequências.

### Dicionários de dados e prevenção de leakage

Cada grupo possui um `DICIONARIO_DADOS.md` com o significado e a unidade das
colunas, cobertura temporal, momento de disponibilidade das exógenas e regras
para impedir que informações futuras entrem no treinamento:

- `grupo1/DICIONARIO_DADOS.md` — Bitcoin;
- `grupo2/DICIONARIO_DADOS.md` — tráfego;
- `grupo3/DICIONARIO_DADOS.md` — poluição;
- `grupo4/DICIONARIO_DADOS.md` — clima;
- `grupo5/DICIONARIO_DADOS.md` — ouro.

A convenção adotada é previsão de um passo à frente antes do início do período
alvo. Medições realizadas dentro do período previsto entram apenas com
defasagem; calendário e eventos conhecidos antecipadamente podem ser usados no
próprio período.

### Integração com os notebooks-base

Os quatro arquivos de `notebooks-base/` já estão conectados às tarefas T01 e
T02. Ao copiar um template para o trabalho do grupo, defina `BASE_NAME` como uma
das opções abaixo:

```python
BASE_NAME = "bitcoin"  # bitcoin, trafego, poluicao, clima ou ouro
```

A célula T01 localiza a raiz do projeto, carrega a base e exibe o relatório
sanitário. A célula T02 encontra e renderiza automaticamente o
`DICIONARIO_DADOS.md` do mesmo grupo.
