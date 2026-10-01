# ProjetoFinal-SeriesTemporais

Projeto final de Séries Temporais contendo quatro modelos de previsão:
SARIMAX, Holt-Winters, Random Forest e MLP Regressor (redes neurais), aplicados
a cinco bases diferentes.

## Features compartilhadas (T06)

`features_temporais.py` implementa o pipeline de atributos dos modelos de
tabela. `configuracao_features(nome)` define lags, janelas e calendário iniciais
para Bitcoin, tráfego, poluição, clima e ouro. `preparar_features_base` aplica a
configuração correspondente; `construir_features_temporais` permite ajustes
explícitos, sem duplicar a lógica nos notebooks. Os notebooks de RF e MLP do
Grupo 4 já chamam esse módulo, assim como os respectivos templates.

```python
from preparacao_bases import carregar_base_tratada
from features_temporais import preparar_features_base

df, meta = carregar_base_tratada('clima')
features = preparar_features_base(
    df, 'clima', meta['alvo'], meta['frequencia'],
    remover_incompletos=True,
)
treino = features.loc[features.index < meta['inicio_teste']]
teste = features.loc[features.index >= meta['inicio_teste']]
X_treino, y_treino = treino.drop(columns='target'), treino['target']
```

Os lags de alvo e exógenas são sempre de períodos anteriores; as médias e
desvios móveis começam em `t-1`. O calendário do instante previsto é conhecido
antecipadamente e recebe seno/cosseno cíclicos. Tráfego também recebe um
indicador de feriado conhecido no calendário. Categorias meteorológicas ficam
fora da configuração inicial porque precisariam de encoding ajustado no treino.
Com `remover_incompletos=False` (padrão), a grade inteira e seus nulos são
preservados para auditoria. Na modelagem, remova linhas incompletas **depois**
de construir os lags e mantenha o corte temporal do Excel. O módulo não ajusta
escala, imputação estatística, encoding aprendido ou modelo: essas etapas
dependem das janelas de T07/T08. As configurações de lags são pontos de partida;
qualquer escolha por desempenho deve usar apenas o treino.

## Random Forest do Grupo 4

Instale `requirements-random-forest.txt` e execute
`grupo4/random-forest-4.ipynb` do início ao fim. O notebook consome o Excel
tratado do Grupo 4 e guarda no próprio `.ipynb` a busca de hiperparâmetros,
as previsões, MAE/RMSE/R², métricas mensais, dispersão dos erros, gráficos,
Ljung-Box e importância das features. Ele não cria arquivos de resultados nem
chama scripts auxiliares. As saídas da última execução permanecem incorporadas
no notebook versionado.

A seleção usa 12 combinações em três janelas expansivas de treino com validações
de seis meses. O teste final ocupa os últimos 20% da grade e não participa da
seleção. A floresta é ajustada uma vez; as entradas são atualizadas hora a hora
para prever a próxima hora. A amostra mensal de 10% é um subconjunto do mesmo
teste, calculada apenas para comparar a estabilidade do MAE. Os resultados
numéricos atuais se referem somente ao Grupo 4.

## Fluxo único de preparação (T01)

Abra **`preparar-bases.ipynb`** na raiz. Ele lê os cinco arquivos originais já
existentes em `grupo1/` a `grupo5/`, aplica o tratamento e publica **um Excel
tratado por grupo** em `dados_tratados/`. Esses cinco Excel são a entrada comum
dos modelos; não são criadas cópias adicionais das fontes.

Para regenerar os mesmos cinco Excel após mudar dados ou regras:

```bash
pip install -r requirements-dados.txt
python preparacao_bases.py --sobrescrever
```

O pequeno `dados_tratados/manifesto.json` registra hashes das fontes e dos cinco
Excel, regras, diagnósticos e o corte de treino/teste. Ele é metadado, não uma
sexta base. Regenerar substitui os mesmos cinco arquivos; os resultados antigos
dos modelos continuam identificados pelo hash da base usada em cada execução.

| Base / grupo | Frequência | Seed | Treino / teste | Excel |
|---|---|---:|---|---|
| Bitcoin / 1 | Diária | 42 | 70% / 30% | `base-tratada-1.xlsx` |
| Tráfego / 2 | Horária | 67 | 80% / 20% | `base-tratada-2.xlsx` |
| Poluição / 3 | Horária | 42 | 80% / 20% | `base-tratada-3.xlsx` |
| Clima / 4 | Horária | 42 | 80% / 20% | `base-tratada-4.xlsx` |
| Ouro / 5 | Semanal, sexta-feira | 42 | 75% / 25% | `base-tratada-5.xlsx` |

Cada Excel contém `dados` (grade temporal e medições) e `metadados` (origem,
protocolo e diagnóstico). As colunas `_alvo_observado`, `_linha_completa` e
`_particao` são controles; o carregador as remove das entradas dos modelos.

```python
import pandas as pd
from preparacao_bases import carregar_base_tratada

df, meta = carregar_base_tratada('clima')
inicio_teste = pd.Timestamp(meta['inicio_teste'])
# Criar lags e janelas sobre a grade completa de df, antes de excluir NaN.
# Depois, dividir as features usando índice < ou >= inicio_teste.
```

O carregador confere o hash do Excel e a regularidade temporal. Os três
notebooks do grupo 4 (`sarimax-4.ipynb`, `random-forest-4.ipynb` e
`mlp-regressor-4.ipynb`) e os quatro templates já consomem essa interface.
Nos templates, escolha `BASE_NAME`; ao copiá-los, use `modelo-grupo.ipynb`.
Os templates ainda exigem suas tarefas de modelagem, sobretudo o Holt-Winters,
cujo ajuste em séries com lacunas precisa ser definido na T09.

`grupo1/holt-winters-1.ipynb`, incorporado da `main`, preserva uma análise
**mensal exploratória** do Bitcoin a partir do Excel tratado. Seus resultados
não substituem o pipeline diário 70%/30% definido para o Grupo 1; essa
adaptação de T09 permanece pendente.

### Regras e limites do tratamento

- Datas inválidas são removidas e contadas; datas válidas ficam em ordem.
- Duplicatas exatas são removidas. Em timestamps repetidos, preserva-se a
  primeira linha inteira, com ordem estável. Alvos conflitantes no mesmo
  instante ficam ausentes e são contados, evitando escolher um valor arbitrário.
- Sentinelas `-9999`, infinitos e valores negativos em grandezas não negativas
  viram ausentes. Em tráfego, temperaturas em Kelvin menores ou iguais a zero
  também viram ausentes; ausência de feriado vira `No Holiday`.
- Clima é agregado por hora: médias, máximo de `max. wv (m/s)` e direção
  circular via seno/cosseno. A hora é rotulada pelo início, intervalo fechado
  à esquerda. As medições só ficam disponíveis ao término desse intervalo.
- Ouro converte `.` em ausente e usa o último preço numérico da semana
  `W-FRI`. A última semana pode conter apenas parte dos dias. A origem oficial
  da adaptação segue pendente do link; foi usada a base local do grupo.
- Bitcoin mantém o horário UTC da fonte, sem timezone no Excel. Os campos
  `timeClose`, `timeHigh` e `timeLow` não entram na tabela de modelagem.
- A grade completa é preservada. O alvo **nunca é imputado**. Exógenas podem
  receber o último valor passado por até 6 horas ou 1 dia, conforme a base.
  Ausências remanescentes ficam em branco, com indicadores explícitos.
- Um Excel tratado pode conter ausências reais. Elas não são convertidas em
  zero; não se pode remover datas antes dos lags e comprimir o tempo. Cada
  modelo deve selecionar exemplos elegíveis e avaliar apenas alvos observados.
- O split é cronológico, calculado sobre a grade completa: `int(n * treino)`.
  O corte registrado permanece o mesmo após a criação das features. Em
  previsão de um passo, usar observações anteriores do teste como lags é
  permitido somente quando já estariam disponíveis na origem da previsão.
- Normalização, encoding e imputações estatísticas permanecem no treino de
  cada janela. Medições contemporâneas continuam exigindo defasagem, conforme
  os dicionários. Valores extremos plausíveis permanecem para decisão na T03.

O diagnóstico das fontes e o resumo dos Excel tratados ficam no notebook
`preparar-bases.ipynb`; os detalhes também constam nos metadados dos Excel.

Verificação do tratamento (sem treinar os modelos):

```bash
python -m unittest discover -s tests -v
```

## Validação das bases

O arquivo `validacao_bases.py` centraliza o carregamento e as verificações das
fontes originais de:

- valores nulos;
- linhas e datas duplicadas;
- datas inválidas e ordenação cronológica;
- frequência regular, respeitando a periodicidade própria de cada base.

Uso em notebook ou script:

```python
from validacao_bases import (
    relatorios_como_dataframe,
    validar_todas_bases,
)

# Valida diretamente as cinco bases originais, sem copiá-las.
relatorios = validar_todas_bases()
resumo = relatorios_como_dataframe(relatorios)
display(resumo)
```

A validação é somente leitura: os dados brutos não são corrigidos ou alterados
automaticamente. A preparação dos Excel tratados fica em `preparacao_bases.py`.

As granularidades de modelagem adotadas são: diária para Bitcoin, horária para
tráfego, poluição e clima, e semanal (fechamento na sexta-feira) para ouro.

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
