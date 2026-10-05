# Produção das bases e estado dos 20 modelos

Este guia registra o fluxo usado para preparar as cinco bases e o estado dos
experimentos em 5 de outubro de 2026. Há um notebook por par `modelo-grupo` e
um Excel tratado por grupo. As saídas dos modelos ficam nos próprios notebooks.

## 1. Como as bases foram produzidas

1. `validacao_bases.py` lê e audita as fontes originais nas pastas `grupo1/` a
   `grupo5/`.
2. `preparacao_bases.py`, executado diretamente ou por `preparar-bases.ipynb`,
   elimina duplicatas, trata sentinelas e valores inválidos, estabelece a grade
   temporal e preenche apenas algumas variáveis explicativas com valores
   anteriores. O alvo ausente continua ausente.
3. O processo exporta `dados_tratados/base-tratada-1.xlsx` até
   `base-tratada-5.xlsx`. `dados_tratados/manifesto.json` guarda os hashes,
   cortes e diagnósticos; não é uma sexta base.
4. Cada notebook chama `carregar_base_tratada`, que confere hash, frequência e
   protocolo antes de carregar o Excel. Features e escalas específicas de cada
   família são produzidas depois do corte, com informação disponível na origem.

| Grupo | Base | Alvo | Frequência | Seed | Treino / teste |
|---:|---|---|---|---:|---:|
| 1 | Bitcoin | `priceClose` | Diária | 42 | 70% / 30% |
| 2 | Tráfego | `traffic_volume` | Horária | 67 | 80% / 20% |
| 3 | Poluição | `PM2.5` | Horária | 42 | 80% / 20% |
| 4 | Clima | `T (degC)` | Horária | 42 | 80% / 20% |
| 5 | Ouro | `VALUE` | Semanal, `W-FRI` | 42 | 75% / 25% |

O corte é cronológico e não embaralha observações; a seed controla apenas
etapas estocásticas do ajuste. `features_temporais.py` contém as transformações
compartilhadas; `t08_walk_forward.ipynb` e `walk_forward.py` documentam as
origens elegíveis. A frequência e o corte são definidos no manifesto, não
separadamente em cada experimento.

## 2. Protocolo de avaliação

O objetivo comum é prever **um período à frente**: um dia, uma hora ou uma
semana. Em cada origem do teste, o modelo recebe somente observações e
variáveis que já estariam disponíveis naquele instante. A busca de parâmetros
usa validações cronológicas dentro do treino; o teste é reservado à avaliação.
O Random Forest e o MLP atualizam as entradas em cada origem sem necessariamente
reajustar seus pesos; Holt-Winters e SARIMAX atualizam seus estados conforme o
código de cada notebook.

**A comparação entre os quatro modelos de uma base usa a interseção exata das
datas previstas.** Cada notebook guarda `data`, `real` e `previsto` em uma saída
compactada dentro do próprio `.ipynb`, com exceção do SARIMAX 4, cuja série
datada ainda precisa ser salva. `comparacao-20-modelos.ipynb` descompacta as
séries disponíveis, confere as datas oficiais T08, confronta os valores reais
com o Excel tratado, faz a interseção e recalcula cada MAE nesse mesmo recorte.
Também confere que o MAE reconstruído corresponde ao valor salvo no notebook
de origem. Essa conferência está completa para os grupos 1, 2, 3 e 5.
Contagens iguais, por si só, não bastam para declarar datas iguais. Não se
comparam MAEs de bases diferentes, pois alvos e unidades diferem.

## 3. Ranking por base

Os MAEs abaixo são calculados nas **mesmas datas entre os quatro modelos da
respectiva base**. Menor MAE é melhor. No clima, a ordem usa o MAE salvo do
SARIMAX 4 nas 13.785 datas oficiais; sua reprodução datada ainda precisa ser
incorporada ao notebook. Os cinco grupos cobrem todas as origens
T08 elegíveis; a cobertura percentual é em relação à grade completa do teste,
que pode conter alvos e features ausentes. A tabela detalhada, com datas de
início/fim e todos os MAEs, está em `comparacao-20-modelos.ipynb`.

| Base | 1º | 2º | 3º | 4º | Datas comuns | Cobertura da grade |
|---|---|---|---|---|---:|---:|
| Bitcoin | SARIMAX 1391,9008 | MLP 1401,8277 | Holt-Winters 1404,1918 | Random Forest 1661,4218 | 884 | 100% |
| Tráfego | Random Forest 153,2877 | MLP 180,4071 | Holt-Winters 332,7024 | SARIMAX 351,8835 | 10.267 | 97,68% |
| Poluição | Random Forest 9,8670 | Holt-Winters 10,3912 | MLP 10,6862 | SARIMAX 32,2177 | 6.336 | 90,35% |
| Clima | MLP 0,3821 | Random Forest 0,3950 | SARIMAX 0,4122 | Holt-Winters 0,6866 | 13.785 | 98,28% |
| Ouro | SARIMAX 19,5104 | Holt-Winters 19,5735 | MLP 22,6521 | Random Forest 36,1629 | 601 | 100% |

No Bitcoin, a vantagem do SARIMAX sobre o MLP é pequena (aproximadamente
0,71% do MAE do segundo colocado); no ouro, a vantagem sobre Holt-Winters é
aproximadamente 0,32%. O ranking ordena o erro observado, sem demonstrar que
essas pequenas diferenças seriam estáveis em outro período. Nos grupos 1 e 5,
o MLP foi revisado após inspeção do teste, então sua posição é exploratória.
O SARIMAX 4 tem avisos de não convergência: a posição dele descreve o ajuste
salvo, sem comprovar estabilidade dos parâmetros.

### Random Forest

Há cinco notebooks com busca temporal, previsão de um passo, métricas e
análise de features. Os grupos 2 e 3 também experimentam perfis reduzidos de
features para aumentar cobertura, sem alterar por si só as origens oficiais.
O grupo 4 foi executado integralmente: 18 de 18 células, MAE 0,3950 em 13.785
horas e cobertura de 98,28% da grade de teste. A previsão é walk-forward quanto
às entradas; isso não significa que a floresta seja reajustada em toda hora.

### Holt-Winters

O commit `502bb47` da `main` foi incorporado à `dev`. Ele passa a preparar a
série separadamente em cada origem, sem interpolar um valor de treino com uma
observação posterior à origem, e examina erros fora da amostra. Os cinco
notebooks preservam o estudo original de horizontes múltiplos como análise
adicional e incluem ao final uma avaliação executada de **um passo** na grade
completa, com atualização causal do estado e sem inventar alvos ausentes. Nessa
avaliação de um passo, a configuração é escolhida na validação pré-teste.
Foram escolhidas tendência no grupo 1, tendência com sazonalidade no grupo 2 e
somente nível nos grupos 3, 4 e 5. Os ajustes finais declararam convergência.
Holt-Winters melhora claramente a persistência no tráfego (MAE 332,7024 contra
590,7910); em Bitcoin, poluição, clima e ouro fica próximo ou pior que ela.

O estudo antigo ainda usa blocos de 30 dias, 168 horas ou 13 semanas, conforme
a base, e não deve ser misturado aos MAEs de um passo. As seções antigas dos
grupos 3 e 4 aparecem parcialmente executadas nos arquivos salvos após o
commit novo; elas precisam de uma execução completa antes de citar seus
gráficos e diagnósticos multipasso. As seções novas de um passo têm resultado
salvo para os cinco grupos.

### SARIMAX

Os grupos 2 e 3 tinham análises anteriores que comprimiam lacunas da série e
cobriam respectivamente 7.720 de 10.267 e 3.023 de 6.336 origens. Esses
valores permanecem apenas como exploração. As novas seções de um passo mantêm
a grade horária, tratam o alvo ausente como ausência, fazem seleção no treino
e avaliam as 10.267 e 6.336 origens. No grupo 3, o MAE novo é bem pior que a
referência de persistência (32,2177 contra 10,3906); isso deve ser discutido,
não escondido. No grupo 4, ainda há avisos de convergência a investigar antes
de considerar o ajuste estabilizado.

### MLP Regressor

Os cinco notebooks estão presentes e têm avaliação salva. Nos grupos 1 e 5,
o modelo foi revisado depois de o erro do teste ter sido visto. Por isso,
esses MAEs são **exploratórios**: a escolha de hiperparâmetros dentro do treino
não apaga o uso do teste para decidir a revisão. O relatório deve explicitar
essa limitação.

## 4. O que falta para fechar a entrega

1. Reproduzir integralmente as seções antigas de Holt-Winters 3 e 4, ou
   apresentar apenas as seções de um passo já executadas.
2. Investigar a convergência do SARIMAX 4 e registrar se o ajuste escolhido é
   estável. Explicar o desempenho do SARIMAX 3 frente à persistência.
3. No relatório e na apresentação, separar resultados de um passo dos
   estudos multipasso e exploratórios; incluir cobertura, datas, gráficos de
   previsão e erro, resíduos, importância de features e limitações.

## 5. Como reproduzir

Instale as dependências indicadas no `README.md`. Para regenerar as mesmas
cinco bases, execute `python preparacao_bases.py --sobrescrever`. Abra cada
notebook `grupoN/modelo-N.ipynb` e use **Restart & Run All**. Os notebooks de
Holt-Winters têm uma seção de um passo autônoma ao final; execute-a mesmo se
interromper o estudo multipasso anterior. Depois execute
`comparacao-20-modelos.ipynb`. Ele relê as séries compactadas nas saídas dos
notebooks e refaz o ranking; se faltar alguma série, mostra a pendência em vez
de produzir uma colocação parcial para aquela base. Para atualizar um modelo,
execute novamente também a célula final que incorpora suas previsões no
notebook antes de refazer a comparação.
