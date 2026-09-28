# Dicionário de dados e disponibilidade temporal — Poluição

## Escopo e hipótese de previsão

- Arquivo: `PRSA_Data_Aotizhongxin_20130301-20170228.csv`.
- Registros: 35.064 linhas e 18 colunas.
- Período observado: 01/03/2013 00:00 a 28/02/2017 23:00.
- Granularidade de modelagem: horária.
- Estação: Aotizhongxin, Beijing.
- Alvo assumido: `PM2.5` da próxima hora.
- Origem da previsão: final da hora `t-1`, antes do início da hora `t`.

As definições e unidades seguem a documentação do conjunto
[Beijing Multi-Site Air Quality no UCI](https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality).
Se o grupo escolher outro poluente como alvo, a classificação da respectiva
coluna deve mudar de exógena para alvo.

## Dicionário de dados

| Coluna | Tipo | Significado | Unidade | Papel | Disponibilidade temporal |
|---|---|---|---|---|---|
| `No` | inteiro | Número sequencial da linha | sem unidade | Identificador | Existe no arquivo, mas não representa fenômeno e deve ser excluído do modelo. |
| `year` | inteiro | Ano da observação | ano | Índice/calendário | Conhecido antecipadamente. |
| `month` | inteiro | Mês da observação | 1–12 | Índice/calendário | Conhecido antecipadamente. |
| `day` | inteiro | Dia do mês | 1–31 | Índice/calendário | Conhecido antecipadamente. |
| `hour` | inteiro | Hora da observação | 0–23 | Índice/calendário | Conhecido antecipadamente. |
| `PM2.5` | decimal | Concentração de material particulado fino | µg/m³ | **Alvo** | Medição da hora, disponível após aquisição/publicação. |
| `PM10` | decimal | Concentração de material particulado | µg/m³ | Exógena candidata | Medição da hora, disponível após aquisição/publicação. |
| `SO2` | decimal | Concentração de dióxido de enxofre | µg/m³ | Exógena candidata | Medição da hora, disponível após aquisição/publicação. |
| `NO2` | decimal | Concentração de dióxido de nitrogênio | µg/m³ | Exógena candidata | Medição da hora, disponível após aquisição/publicação. |
| `CO` | decimal | Concentração de monóxido de carbono | µg/m³ | Exógena candidata | Medição da hora, disponível após aquisição/publicação. |
| `O3` | decimal | Concentração de ozônio | µg/m³ | Exógena candidata | Medição da hora, disponível após aquisição/publicação. |
| `TEMP` | decimal | Temperatura | °C | Exógena candidata | Observação meteorológica da hora. |
| `PRES` | decimal | Pressão atmosférica | hPa | Exógena candidata | Observação meteorológica da hora. |
| `DEWP` | decimal | Temperatura do ponto de orvalho | °C | Exógena candidata | Observação meteorológica da hora. |
| `RAIN` | decimal | Precipitação | mm | Exógena candidata | Acumulado/observação da hora. |
| `wd` | categórica | Direção do vento | categoria cardinal | Exógena candidata | Observação meteorológica da hora. |
| `WSPM` | decimal | Velocidade do vento | m/s | Exógena candidata | Observação meteorológica da hora. |
| `station` | categórica | Nome da estação de monitoramento | categoria | Identificador estático | Conhecido, mas constante nesta base e sem poder explicativo interno. |

## Disponibilidade temporal e risco de leakage

Os poluentes e dados meteorológicos da linha `t` são medições realizadas na
hora que se deseja prever. Sem documentação de latência ou histórico de
publicação, a política conservadora é considerá-los indisponíveis antes de `t`.

| Uso | Variáveis | Regra |
|---|---|---|
| Seguro no próprio `t` | `year`, `month`, `day`, `hour` e calendário derivado | São conhecidos antes da hora-alvo. |
| Seguro somente com defasagem | Poluentes, `TEMP`, `PRES`, `DEWP`, `RAIN`, `wd`, `WSPM` | Usar valores de `t-1` ou anteriores. |
| Remover | `No`, `station` | `No` é apenas sequência; `station` tem um único valor neste arquivo. |
| Proibido de forma contemporânea | `PM2.5_t` e demais medições realizadas em `t` | Ainda não estavam disponíveis na origem da previsão. |

Uma previsão meteorológica emitida antes de `t` poderia ser usada, mas ela não
existe neste arquivo. O clima observado não deve ser tratado como se fosse uma
previsão perfeita.

## Disponibilidade e faltantes

- A grade horária está completa e ordenada, mas 3.249 linhas têm pelo menos um
  valor nulo.
- Nulos relevantes: `PM2.5` 925; `PM10` 718; `SO2` 935; `NO2` 1.023;
  `CO` 1.776; `O3` 1.719; `wd` 81.
- Imputação temporal não pode consultar observações posteriores à origem da
  previsão. Interpolação bidirecional sobre a série inteira produz leakage.
- Uma opção segura em produção é imputação causal: último valor conhecido,
  mediana histórica por hora/mês calculada no treino ou modelo de imputação
  ajustado apenas com o passado.

## Regras de engenharia e avaliação

1. Construir `data_hora` com `year`, `month`, `day` e `hour` e ordenar.
2. Criar todos os lags antes de qualquer janela móvel.
3. Ajustar imputadores, escaladores e codificadores apenas no treino.
4. Se houver atributos de outros poluentes, defasá-los em pelo menos uma hora.
5. Fazer divisão cronológica e backtesting com janela expansiva ou deslizante.
6. Registrar a latência real dos sensores caso o projeto passe a simular uso
   operacional; a defasagem mínima deve ser maior ou igual a essa latência.

## Decisão operacional

- **Permitidas:** calendário contemporâneo e todas as medições históricas.
- **Condicionais:** previsões meteorológicas com emissão anterior à hora-alvo.
- **Bloqueadas:** poluentes e meteorologia realizados na própria hora prevista.

