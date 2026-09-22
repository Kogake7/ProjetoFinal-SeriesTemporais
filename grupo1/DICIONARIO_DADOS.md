# Dicionário de dados e disponibilidade temporal — Bitcoin

## Escopo e hipótese de previsão

- Arquivo: `bitcoin.xlsx`.
- Registros: 2.922 linhas e 9 colunas.
- Período observado: 22/08/2018 12:00 UTC a 13/09/2026 12:00 UTC, considerando `timeOpen`.
- Granularidade de modelagem: diária.
- Alvo assumido: `priceClose` do dia seguinte.
- Origem da previsão: fechamento do dia `t-1`, antes da abertura do período `t`.

O arquivo não contém metadados sobre a corretora, o ativo/par, a moeda dos
preços ou a definição de `volume`. Essas informações precisam ser confirmadas
com a fonte original antes da apresentação final.

## Dicionário de dados

| Coluna | Tipo no arquivo | Significado | Unidade | Papel | Disponibilidade temporal |
|---|---|---|---|---|---|
| `timeOpen` | inteiro | Início do intervalo diário em Unix epoch | ms, interpretado em UTC | Índice temporal | O instante de calendário é conhecido antecipadamente. |
| `timeClose` | inteiro | Fim do intervalo diário em Unix epoch | ms, interpretado em UTC | Metadado temporal | O limite planejado é conhecido, mas o registro só fica completo após o fechamento. |
| `timeHigh` | inteiro | Instante em que ocorreu a máxima do período | ms, interpretado em UTC | Exógena candidata | Ex post: só é conhecido após o período terminar. |
| `timeLow` | inteiro | Instante em que ocorreu a mínima do período | ms, interpretado em UTC | Exógena candidata | Ex post: só é conhecido após o período terminar. |
| `priceOpen` | decimal | Preço de abertura do período | moeda não informada | Exógena candidata | Só fica conhecido na abertura; não está disponível na previsão feita em `t-1`. |
| `priceHigh` | decimal | Maior preço do período | moeda não informada | Exógena candidata | Só fica consolidado ao fim do período. |
| `priceLow` | decimal | Menor preço do período | moeda não informada | Exógena candidata | Só fica consolidado ao fim do período. |
| `priceClose` | decimal | Preço de fechamento do período | moeda não informada | **Alvo** | Só fica conhecido ao fim do período. |
| `volume` | decimal | Volume negociado reportado no período | unidade não informada | Exógena candidata | Só fica consolidado ao fim do período. |

## Disponibilidade temporal e risco de leakage

Na hipótese adotada, nenhuma variável OHLCV do dia `t` está disponível no
momento de prever `priceClose_t`. Portanto:

| Uso | Variáveis | Regra |
|---|---|---|
| Seguro no próprio `t` | Componentes de calendário derivados de `timeOpen` | Dia da semana, mês e componentes cíclicos podem ser calculados antecipadamente. |
| Seguro somente com defasagem | `priceOpen`, `priceHigh`, `priceLow`, `priceClose`, `volume`, `timeHigh`, `timeLow` | Usar valores de `t-1` ou anteriores. |
| Proibido de forma contemporânea | `priceHigh_t`, `priceLow_t`, `priceClose_t`, `volume_t`, `timeHigh_t`, `timeLow_t` | São resultados do próprio período previsto. |

`priceOpen_t` somente seria permitido se a origem da previsão mudasse para
**depois da abertura do dia**. Essa mudança deve ser documentada, pois altera o
problema de previsão e a comparação entre modelos.

## Regras de engenharia de atributos

1. Ordenar a base em ordem cronológica crescente antes de qualquer divisão; o
   arquivo atual está em ordem decrescente.
2. Criar lags com `shift(1)` ou maior. Exemplo seguro:
   `priceClose.shift(1).rolling(7).mean()`.
3. Nunca calcular a janela e só depois aplicar `shift`, pois isso pode incluir o
   fechamento do próprio dia-alvo.
4. Calcular retornos usados como entrada apenas até `t-1`.
5. Ajustar imputação, escala e seleção de atributos apenas no treino.
6. Fazer treino, validação e teste por blocos cronológicos, sem embaralhamento.

## Decisão operacional

- **Permitidas:** calendário do dia previsto e todas as variáveis de mercado
  corretamente defasadas.
- **Bloqueadas:** máximas, mínimas, fechamento, volume e horários de máxima ou
  mínima do mesmo dia previsto.
- **Pendente:** confirmar ativo/par, moeda, fuso e unidade de volume na fonte.

