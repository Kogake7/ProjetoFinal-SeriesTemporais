# Dicionário de dados e disponibilidade temporal — Clima

## Escopo e hipótese de previsão

- Arquivo: `jena_climate_2009_2016.csv`.
- Registros brutos: 420.551 linhas e 15 colunas.
- Período observado: 01/01/2009 00:10 a 01/01/2017 00:00.
- Coleta original: aproximadamente a cada 10 minutos.
- **Granularidade oficial de modelagem: horária.**
- Alvo assumido: `T (degC)` da próxima hora.
- Origem da previsão: fechamento da hora `t-1`, antes da hora `t`.

Os dados são da estação meteorológica do Max Planck Institute for
Biogeochemistry em Jena. A página do instituto disponibiliza os
[arquivos meteorológicos](https://www.bgc-jena.mpg.de/wetter/weather_data.html),
e o tutorial oficial do
[TensorFlow](https://www.tensorflow.org/tutorials/structured_data/time_series)
documenta este recorte de 2009–2016 e seu uso em previsão horária.

## Dicionário de dados

| Coluna | Tipo | Significado | Unidade | Papel | Disponibilidade temporal |
|---|---|---|---|---|---|
| `Date Time` | texto/data | Instante da medição | data-hora local | Índice temporal | O calendário é conhecido; o conjunto de medições só fecha após a hora. |
| `p (mbar)` | decimal | Pressão atmosférica | mbar | Exógena candidata | Medida durante a hora. |
| `T (degC)` | decimal | Temperatura do ar | °C | **Alvo** | Medida durante a hora e consolidada ao final. |
| `Tpot (K)` | decimal | Temperatura potencial | K | Exógena candidata | Medida/calculada a partir das condições da hora. |
| `Tdew (degC)` | decimal | Temperatura do ponto de orvalho | °C | Exógena candidata | Medida/calculada na hora. |
| `rh (%)` | decimal | Umidade relativa | % | Exógena candidata | Medida durante a hora. |
| `VPmax (mbar)` | decimal | Pressão de vapor de saturação | mbar | Exógena candidata | Medida/calculada na hora. |
| `VPact (mbar)` | decimal | Pressão de vapor atual | mbar | Exógena candidata | Medida/calculada na hora. |
| `VPdef (mbar)` | decimal | Déficit de pressão de vapor | mbar | Exógena candidata | Medida/calculada na hora. |
| `sh (g/kg)` | decimal | Umidade específica | g/kg | Exógena candidata | Medida/calculada na hora. |
| `H2OC (mmol/mol)` | decimal | Concentração molar de vapor d’água | mmol/mol | Exógena candidata | Medida/calculada na hora. |
| `rho (g/m**3)` | decimal | Densidade do ar | g/m³ | Exógena candidata | Medida/calculada na hora. |
| `wv (m/s)` | decimal | Velocidade do vento | m/s | Exógena candidata | Medida durante a hora. |
| `max. wv (m/s)` | decimal | Velocidade máxima do vento | m/s | Exógena candidata | Só é conhecida depois de completar a janela da hora. |
| `wd (deg)` | decimal | Direção do vento | graus | Exógena candidata | Medida durante a hora. |

## Formação da série horária

O arquivo contém observações de 10 em 10 minutos, mas o produto de modelagem é
horário. A consolidação deve ocorrer **antes** da criação de lags:

- média horária para temperatura, pressão, umidade, densidade, vapor, direção e
  velocidade média;
- máximo horário para `max. wv (m/s)`;
- uma linha por hora, rotulada de forma consistente pelo início ou fim da hora.

Para direção do vento, a média aritmética de graus pode ser inadequada perto de
0°/360°. A opção recomendada é transformar direção e velocidade em componentes
`x = velocidade × cos(direção)` e `y = velocidade × sin(direção)`, agregar as
componentes e, se necessário, reconstruir o ângulo.

## Disponibilidade temporal e risco de leakage

Todos os valores meteorológicos da hora `t`, inclusive sua média e seu máximo,
só ficam completos no encerramento de `t`. Para prever `T_t` antes de a hora
começar, eles não podem ser usados contemporaneamente.

| Uso | Variáveis | Regra |
|---|---|---|
| Seguro no próprio `t` | Calendário derivado de `Date Time` | Hora do dia, dia e ciclo anual são conhecidos antecipadamente. |
| Seguro somente com defasagem | Todas as medições meteorológicas horárias | Usar agregados de `t-1` ou anteriores. |
| Proibido de forma contemporânea | Média/máximo da própria hora `t`, incluindo `T_t` | Exigem observações feitas ao longo da hora prevista. |

As variáveis de umidade e temperatura potencial podem ser derivadas ou muito
correlacionadas com a temperatura. Isso não é leakage quando estão defasadas,
mas exige atenção a multicolinearidade e à interpretação do modelo.

## Qualidade relevante para disponibilidade

- Não há nulos convencionais, mas `wv (m/s)` contém 18 valores `-9999` e
  `max. wv (m/s)` contém 20. Esses são sentinelas inválidos, não velocidades.
- Há 327 timestamps repetidos e a base não está totalmente ordenada.
- Os sentinelas precisam virar `NaN` antes da agregação horária; caso contrário,
  distorcem média, escala e modelos.
- Qualquer preenchimento deve usar somente treino/passado. Não interpolar
  bidirecionalmente antes da separação temporal.

## Regras de engenharia e avaliação

1. Corrigir sentinelas, remover duplicatas exatas, ordenar e agregar por hora.
2. Aplicar `shift(1)` aos agregados horários antes das janelas móveis.
3. Calcular normalização apenas com o conjunto de treino.
4. Separar treino, validação e teste cronologicamente.
5. Ajustar transformações cíclicas de tempo sem consultar o alvo futuro.
6. Em previsão multietapas, não reutilizar observações reais que ainda não
   existiriam em cada horizonte.

## Decisão operacional

- **Permitidas:** calendário da hora-alvo e clima de horas já encerradas.
- **Condicionais:** previsão meteorológica externa, desde que emitida antes da
  origem da previsão e armazenada por versão.
- **Bloqueadas:** quaisquer agregados realizados da própria hora prevista.

