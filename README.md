# Projeto final — Séries Temporais

O projeto compara **SARIMAX, Holt-Winters, Random Forest e MLP Regressor** em
cinco bases: são 20 experimentos planejados. Cada previsão tem horizonte de um
período (dia, hora ou semana, conforme a base). Os números, gráficos e resíduos
de cada modelo ficam no próprio notebook.

## Bases e preparação

`preparar-bases.ipynb` e `preparacao_bases.py` geram **um Excel tratado por
grupo** em `dados_tratados/`. O `manifesto.json` registra os hashes e os cortes;
ele não é uma base adicional. As fontes originais permanecem nas pastas dos
grupos. O alvo não é imputado: horas sem valor real continuam vazias para que a
avaliação não use valores inventados.

| Grupo | Série | Frequência | Seed | Treino / teste | Excel tratado |
|---|---|---|---:|---:|---|
| 1 | Bitcoin | Diária | 42 | 70% / 30% | `base-tratada-1.xlsx` |
| 2 | Tráfego | Horária | 67 | 80% / 20% | `base-tratada-2.xlsx` |
| 3 | Poluição | Horária | 42 | 80% / 20% | `base-tratada-3.xlsx` |
| 4 | Clima | Horária | 42 | 80% / 20% | `base-tratada-4.xlsx` |
| 5 | Ouro | Semanal (`W-FRI`) | 42 | 75% / 25% | `base-tratada-5.xlsx` |

Para regenerar os Excel com as mesmas regras:

```bash
pip install -r requirements-dados.txt
python preparacao_bases.py --sobrescrever
```

Para executar os notebooks de Random Forest, instale também
`requirements-random-forest.txt`.

Os `DICIONARIO_DADOS.md` de cada grupo descrevem as variáveis, suas unidades e
quando cada medição fica disponível. `validacao_bases.py` audita as fontes;
`features_temporais.py` constrói lags, janelas e calendário sem usar medições
futuras. Os notebooks em `notebooks-base/` são pontos de partida, não resultados
dos 20 experimentos.

## Protocolo e comparação

`t08_walk_forward.ipynb` e `walk_forward.py` registram o corte cronológico,
horizonte e origens elegíveis por base. A configuração atual de origens exige
alvo e features T06 completos. Hiperparâmetros são escolhidos em validações
temporais **dentro do treino**; o teste final fica separado. Cada família pode
ter uma política de reajuste diferente, desde que use apenas informação já
disponível na origem da previsão.

Para comparar diretamente o MAE de dois modelos, use **as mesmas datas e os
mesmos valores reais**. Os modelos podem usar features diferentes. Se suas
coberturas diferirem, apresente a cobertura de cada um e compare o MAE na
interseção das datas; uma comparação em toda a grade requer previsões dos
modelos em todas as origens escolhidas. `comparacao-20-modelos.ipynb` mostra a
consolidação parcial e só calcula o ranking final quando houver resultados
comparáveis dos quatro modelos por base.

## Estado dos modelos neste repositório

| Modelo | Notebooks específicos | Situação para a comparação final |
|---|---|---|
| Random Forest | `random-forest-1.ipynb` a `random-forest-5.ipynb`, em `grupo1/` a `grupo5/` | Cinco execuções com busca temporal, teste e métricas. Há experimentos de cobertura adicionais nos grupos 2 e 3. |
| Holt-Winters | `grupo1/holt-winters-1.ipynb` | Protótipo mensal de Bitcoin; ainda precisa do protocolo diário comum. Grupos 2–5 sem pipeline concluído. |
| SARIMAX | `grupo4/sarimax-4.ipynb` | Execução exploratória com tratamento próprio da fonte. Alvo e datas coincidem com o Excel comum, mas a preparação das exógenas difere; falta reproduzir o fluxo T01 comum. Grupos 1–3 e 5 sem pipeline concluído. |
| MLP Regressor | `grupo4/mlp-regressor-4.ipynb` | Código em preparação, sem execução final salva. Grupos 1–3 e 5 sem pipeline concluído. |

O RF usa um modelo ajustado no treino e atualiza as **entradas** a cada previsão
de um passo; isso é avaliação de origem móvel, sem reajustar a floresta a cada
hora. O SARIMAX exploratório do grupo 4 faz reajustes periódicos. O Holt-Winters
mensal do grupo 1 não deve ser colocado no ranking diário.

Os perfis reduzidos de features nos grupos 2 e 3 são **experimentos** dentro dos
respectivos notebooks. Eles mostram validação temporal, MAE nas datas comuns,
MAE nas datas adicionais e cobertura. O perfil reduzido de poluição também tem
uma busca completa própria de hiperparâmetros. Esses perfis ainda não mudam as
origens oficiais T08 nem os resultados da consolidação T16.

## Onde começar

1. Abra `preparar-bases.ipynb` para entender as cinco fontes e os Excel tratados.
2. Leia `t08_walk_forward.ipynb` para conferir cortes, horizonte e origens.
3. Abra o notebook `modelo-grupo.ipynb` para ver busca, previsão, métricas e gráficos.
4. Consulte `comparacao-20-modelos.ipynb` para o andamento da comparação.

Os notebooks guardam as saídas no próprio arquivo; não há uma pasta separada de
resultados ou figuras. Ao ajustar um modelo, registre a cobertura e as datas da
avaliação junto ao MAE.
