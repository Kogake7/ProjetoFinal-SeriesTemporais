# Dicionário de dados e disponibilidade temporal — Tráfego

## Escopo e hipótese de previsão

- Arquivo: `Metro_Interstate_Traffic_Volume.csv`.
- Registros: 48.204 linhas e 9 colunas.
- Período observado: 02/10/2012 09:00 a 30/09/2018 23:00.
- Granularidade de modelagem: horária.
- Alvo: `traffic_volume` da próxima hora.
- Origem da previsão: final da hora `t-1`, antes do início da hora `t`.
- Localização: tráfego sentido oeste da I-94, estação ATR 301, entre
  Minneapolis e St. Paul.

As definições e unidades seguem a documentação do
[UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume).

## Dicionário de dados

| Coluna | Tipo | Significado | Unidade | Papel | Disponibilidade temporal |
|---|---|---|---|---|---|
| `holiday` | categórica | Feriado nacional/regional ou Minnesota State Fair | categoria | Exógena | Calendário conhecido antecipadamente. Ausência de nome significa “não feriado”, não dado desconhecido. |
| `temp` | decimal | Temperatura média observada na hora | K | Exógena | Medição realizada durante a hora; consolidada ao final dela. |
| `rain_1h` | decimal | Chuva ocorrida na hora | mm | Exógena | Acumulado observado, disponível após a hora. |
| `snow_1h` | decimal | Neve ocorrida na hora | mm | Exógena | Acumulado observado, disponível após a hora. |
| `clouds_all` | inteiro | Cobertura de nuvens | % | Exógena | Observação meteorológica da hora. |
| `weather_main` | categórica | Descrição meteorológica resumida | categoria | Exógena | Classificação do tempo observado na hora. |
| `weather_description` | categórica | Descrição meteorológica detalhada | categoria | Exógena | Classificação do tempo observado na hora. |
| `date_time` | texto/data | Hora da coleta em horário local CST, segundo a fonte | data-hora | Índice temporal | Calendário conhecido antecipadamente; o arquivo não carrega informação explícita de fuso. |
| `traffic_volume` | inteiro | Volume horário reportado pelo sensor de tráfego | veículos/hora | **Alvo** | Consolidado ao final da hora. |

## Disponibilidade temporal e risco de leakage

O arquivo contém **tempo meteorológico realizado**, não previsões meteorológicas
com data de emissão. Por isso, para prever a hora `t` antes de ela começar:

| Uso | Variáveis | Regra |
|---|---|---|
| Seguro no próprio `t` | `holiday` e calendário derivado de `date_time` | Feriado, hora do dia, dia da semana e mês são conhecidos antes da previsão. |
| Seguro somente com defasagem | Todas as colunas meteorológicas e `traffic_volume` | Usar `t-1` ou períodos anteriores. |
| Proibido de forma contemporânea | Clima observado da hora `t` e `traffic_volume_t` | Ainda não existiam na origem da previsão. |

Variáveis meteorológicas da hora futura só podem ser usadas contemporaneamente
se forem substituídas por **previsões meteorológicas históricas**, preservando a
data de emissão de cada previsão. Usar o clima efetivamente observado em `t`
simula informação perfeita e superestima o desempenho.

## Pontos específicos da base

- `holiday` possui 48.143 valores lidos como nulos pelo pandas, mas a
  documentação informa que a variável não possui dados faltantes. Esses casos
  devem virar uma categoria explícita, como `No Holiday`.
- Existem 7.629 timestamps além da primeira ocorrência e 17 linhas exatamente
  duplicadas. Um mesmo horário pode ter mais de uma descrição meteorológica.
- Antes da modelagem horária, consolidar para uma linha por `date_time`, sem
  somar repetidamente `traffic_volume`.
- Confirmar se o volume é idêntico nas linhas do mesmo horário; se for, manter
  um único valor do alvo e definir regra determinística para as categorias de
  clima.

## Regras de engenharia e avaliação

1. Criar lags de tráfego e clima com `shift(1)` antes de médias móveis.
2. Categorias e codificadores devem ser ajustados somente no treino.
3. Imputação e escala devem ser ajustadas somente no treino.
4. Dividir treino, validação e teste cronologicamente.
5. Em backtesting, gerar cada previsão apenas com dados disponíveis até sua
   origem temporal.

## Decisão operacional

- **Permitidas:** calendário e feriado contemporâneos; tráfego e clima passados.
- **Condicionais:** previsão meteorológica contemporânea, somente com histórico
  de versões e horário de emissão.
- **Bloqueadas:** clima realizado e volume de tráfego da própria hora-alvo.

