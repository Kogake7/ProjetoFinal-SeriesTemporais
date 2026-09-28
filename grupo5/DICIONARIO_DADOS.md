# Dicionário de dados e disponibilidade temporal — Ouro

## Escopo e hipótese de previsão

- Arquivo: `gold.daily.prices.csv`.
- Registros brutos: 12.009 linhas e 2 colunas.
- Período observado: 01/04/1968 a 10/04/2014.
- Frequência original: dias úteis.
- **Granularidade oficial de modelagem: semanal.**
- Alvo: último `VALUE` disponível da semana encerrada na sexta-feira (`W-FRI`).
- Origem da previsão: encerramento da semana `t-1`, antes da semana `t`.

O arquivo local não traz nome da série, instituição, moeda, unidade nem horário
de fixação. Os valores são compatíveis com uma série histórica de preço diário
do ouro, mas a definição exata precisa ser confirmada na origem antes de chamar
`VALUE` de USD por onça troy. Séries de preços de ouro da LBMA foram removidas
do FRED em 2022, conforme o
[comunicado do Federal Reserve Bank of St. Louis](https://news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/),
o que também impede usar o antigo link como prova definitiva da procedência
deste arquivo.

## Dicionário de dados

| Coluna | Tipo no arquivo | Significado | Unidade | Papel | Disponibilidade temporal |
|---|---|---|---|---|---|
| `DATE` | texto/data | Data do valor diário | data | Índice temporal | Calendário conhecido antecipadamente. |
| `VALUE` | texto, deve virar decimal | Preço/cotação diária do ouro | não confirmada | **Alvo diário de origem e alvo semanal após agregação** | O valor diário só está disponível depois da publicação/fixação correspondente. |

## Formação da série semanal

Para cada semana `W-FRI`, o alvo é o último `VALUE` numérico disponível naquela
semana. A data do rótulo semanal é a sexta-feira, mesmo quando o último valor
veio de um dia anterior por feriado ou ausência de publicação.

Essa regra precisa permanecer idêntica em treino e produção. Se o objetivo for
prever **média semanal**, será outro alvo e deverá ser documentado; não se deve
alternar entre média e último valor conforme a disponibilidade.

## Disponibilidade temporal e risco de leakage

A base não possui exógenas observadas: há apenas data e alvo. As variáveis de
entrada possíveis são calendário e histórico defasado do próprio preço.

| Uso | Variáveis | Regra |
|---|---|---|
| Seguro no próprio `t` | Calendário da semana | Número da semana, mês, trimestre e feriados podem ser conhecidos antes. |
| Seguro somente com defasagem | `VALUE`, retornos, médias e volatilidade | Usar semana `t-1` ou anteriores. |
| Proibido de forma contemporânea | Último preço, média, máximo ou mínimo da semana `t` | Dependem de valores publicados durante a semana que está sendo prevista. |

Ao prever o fechamento semanal antes da segunda-feira, nem mesmo o preço de
segunda da semana-alvo pode entrar. Se a origem mudar para durante a semana, o
problema passa a ser nowcasting e precisa de avaliação própria.

## Qualidade relevante para disponibilidade

- `VALUE` é lida como texto porque existem 368 ocorrências do marcador `.`.
- O marcador `.` deve virar `NaN` antes da conversão numérica.
- Um `.` não pode ser convertido para zero: zero seria um preço artificial.
- Ao formar a semana, usar o último valor numérico disponível; registrar semanas
  sem qualquer observação válida como ausentes.
- Forward fill através de longos intervalos pode criar semanas artificiais e
  deve ser limitado ou evitado.

## Regras de engenharia e avaliação

1. Converter `DATE`, trocar `.` por ausente e converter `VALUE` para decimal.
2. Ordenar cronologicamente e agregar com `resample('W-FRI').last()`.
3. Criar `lag_1`, retornos e janelas somente depois da agregação semanal.
4. Aplicar `shift(1)` antes de médias/volatilidades usadas como atributos.
5. Ajustar escala, imputação e hiperparâmetros somente no treino.
6. Usar divisões cronológicas e walk-forward validation, nunca divisão aleatória.
7. Se novas exógenas econômicas forem adicionadas, guardar também a data de
   publicação e usar o valor/vintage que existia na origem de cada previsão.

## Decisão operacional

- **Permitidas:** calendário conhecido e histórico semanal defasado.
- **Condicionais:** novas variáveis macroeconômicas com calendário de publicação
  e vintages históricos.
- **Bloqueadas:** qualquer estatística calculada com preços da própria semana
  que está sendo prevista.
- **Pendente:** confirmar série, moeda, unidade e horário de publicação.

