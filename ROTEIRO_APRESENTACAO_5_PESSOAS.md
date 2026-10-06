# Roteiro de apresentação para cinco pessoas

Este roteiro acompanha `relatorio-projeto.html`. Os nomes seguem a divisão de
tarefas e o roteiro recebidos em PDF: Felipe (Felipão), Júlia, Sofia, Martins e
Dmitri. A distribuição abaixo dá a cada responsável pelo modelo uma fala
própria e reserva a Felipe as bases, o método comum e a condução da apresentação.

## Antes de começar

- Abram o HTML localmente e deixem um notebook de cada família disponível caso
  alguém peça detalhes. O HTML concentra os resultados; gráficos de busca,
  importância e diagnóstico mais específicos permanecem nos notebooks.
- Para preparar respostas sobre resíduos, sazonalidade, viés e limites dos
  testes, leiam `ANALISE_DIAGNOSTICA_RESULTADOS.md` antes do ensaio.
- Uma pessoa controla o computador, preferencialmente Felipe. Cliquem nas abas
  da seção **04 Modelos** e nos botões de base da seção **05 Resultados** quando
  o respectivo apresentador pedir. Evitem trocar de base enquanto alguém explica.
- Sugestão de duração: 18 a 22 minutos, cerca de 3 minutos por modelo, 4 minutos
  para abertura e método e 3 a 5 minutos para comparação e conclusão. Ajustem ao
  limite real da banca.
- Em todos os resultados, **MAE menor é melhor**. Cada MAE está na unidade do
  respectivo alvo. Não comparem numericamente o MAE de bases diferentes.
- O ranking usa as datas comuns aos quatro modelos **dentro de cada base** e
  previsão de **um passo**: um dia para Bitcoin, uma hora para tráfego, poluição
  e clima, e uma semana para ouro.

## Ordem, navegação e passagem de fala

| Ordem | Pessoa | Onde clicar no HTML | Tempo sugerido | Mensagem principal |
|---:|---|---|---:|---|
| 1 | Felipe | 01 Contexto, 02 Dados, 03 Protocolo | 4 min | Cinco bases, quatro modelos, corte cronológico e comparação justa. |
| 2 | Júlia | 04 Modelos → Holt-Winters | 3 min | Referência estatística de nível, tendência e sazonalidade; resultado oficial de um passo. |
| 3 | Sofia | 04 Modelos → SARIMAX | 3 min | Dependência temporal, sazonalidade e exógenas; duas vitórias e limitações. |
| 4 | Martins | 04 Modelos → Random Forest | 3 min | Features causais, busca temporal e duas vitórias. |
| 5 | Dmitri | 04 Modelos → MLP | 3 min | Rede, escalonamento e vitória no clima. |
| 6 | Sofia, com Felipe moderando | 05 Resultados, 06 Cobertura, 07 Conclusão | 4–6 min | Ranking por base, interpretação, ressalvas e fechamento. |

Felipe pode anunciar a troca de seção e controlar o tempo. Quando aparecer uma
pergunta sobre uma base específica, ele dá o contexto da base e passa a questão
técnica ao dono do modelo. Todos devem conhecer a tabela final, mesmo que Sofia
faça a leitura principal.

## 1. Felipe — contexto, cinco bases e protocolo

**HTML:** início, 01 Contexto, 02 Dados e 03 Protocolo. Percorra as cinco abas
das bases sem ler cada cartão inteiro.

**Fala sugerida:**

> Nosso objetivo é testar como quatro abordagens diferentes se comportam em
> cinco séries temporais reais. A pergunta é: qual produz o menor erro de
> previsão fora da amostra em cada contexto? Temos vinte combinações de modelo
> e base. Escolhemos o MAE como medida principal porque ele é o erro absoluto
> médio na unidade da variável prevista.
>
> As bases são deliberadamente diferentes. Bitcoin é diário, com preço de
> fechamento como alvo e divisão de 70% para treino e 30% para teste. Tráfego,
> poluição e clima são horários, cada um com divisão 80/20. O tráfego prevê
> volume de veículos; a poluição prevê PM2.5; o clima prevê temperatura em graus
> Celsius. O ouro foi agregado por semana, com divisão 75/25. As sementes são
> 42, exceto no tráfego, que usa 67; elas controlam etapas aleatórias, não
> embaralham o corte temporal.
>
> Partimos das fontes originais, verificamos datas, duplicatas, frequência,
> valores faltantes e disponibilidade das variáveis externas. Cada grupo tem
> exatamente um Excel tratado em `dados_tratados/`. O alvo ausente não foi
> inventado. As features, como atrasos, médias móveis e calendário, só usam
> informação que já existia quando a previsão seria feita.
>
> O teste é o trecho final da série. A escolha dos hiperparâmetros usa apenas
> validação cronológica dentro do treino. No teste, caminhamos origem por
> origem e prevemos um período à frente. Como os modelos podem prever
> quantidades diferentes de instantes, comparamos os quatro somente na
> interseção das datas previstas. Assim todos são avaliados contra os mesmos
> valores reais naquela base.

**Ao mostrar 03 Protocolo:** a palavra *walk-forward* descreve o avanço da
origem de previsão, não exige reajustar todos os modelos em cada passo. RF e
MLP ficam com os parâmetros fixos no teste e recebem entradas atualizadas;
Holt-Winters atualiza o estado; SARIMAX tem reajustes periódicos. É importante
falar essa diferença se a banca perguntar.

**Passagem:** “Com as regras comuns estabelecidas, a Júlia começa pelo modelo
estatístico de suavização, que serve como uma referência estrutural.”

## 2. Júlia — Holt-Winters

**HTML:** 04 Modelos → aba **Holt-Winters**. Na comparação final, a coluna do
Holt-Winters aparece nas cinco bases.

**Fala sugerida:**

> Holt-Winters é uma família de suavização exponencial. Ela tenta representar
> o nível atual da série, uma possível tendência e, quando faz sentido, um
> padrão sazonal. É uma referência importante porque modela a estrutura
> temporal de forma relativamente simples e interpretável, sem depender da
> mesma engenharia de atributos do RF e da MLP.
>
> Nós mantivemos o estudo antigo de previsões de vários passos como análise
> adicional. Para a comparação oficial, acrescentamos uma avaliação causal de
> apenas um passo nas cinco bases. A configuração foi escolhida por validação
> dentro do treino. No resultado final, Bitcoin usa tendência; tráfego usa
> tendência e sazonalidade; poluição, clima e ouro usam somente nível. O estado
> é atualizado à medida que novas observações ficam disponíveis.
>
> Nas datas comuns, os MAEs foram 1.404,19 no Bitcoin, 332,70 no tráfego,
> 10,39 na poluição, 0,6866 no clima e 19,57 no ouro. O modelo ficou em segundo
> na poluição e no ouro e muito próximo dos primeiros em Bitcoin e ouro. No
> tráfego, capta parte do padrão temporal, mas RF e MLP erraram menos.

**Se perguntarem sobre STL:** a decomposição separa tendência, sazonalidade e
resíduo e ajuda a decidir quais componentes vale testar. O HTML não contém os
gráficos completos de STL; eles estão nos notebooks. Não afirmem que uma
sazonalidade é forte em todas as bases. A opção final foi selecionada com
validação, não somente por inspeção visual.

**Ressalva indispensável:** não misturar os MAEs do estudo multipasso antigo
com o ranking de um passo. As seções multipasso dos grupos 3 e 4 têm execução
parcial nos arquivos salvos; usem somente a seção oficial de um passo ao citar
o ranking.

**Passagem:** “Agora a Sofia mostra um modelo estatístico que também lida com
dependência temporal, mas pode incluir variáveis externas: o SARIMAX.”

## 3. Sofia — SARIMAX

**HTML:** 04 Modelos → aba **SARIMAX**. Volte à seção 05 para apontar as duas
vitórias quando falar dos resultados.

**Fala sugerida:**

> O SARIMAX combina três ideias: uma parte autorregressiva, que usa o passado;
> diferenciação, para lidar com mudanças de nível; e uma parte de médias móveis
> dos erros. As letras sazonais P, D e Q reproduzem essa estrutura em um ciclo
> de tamanho `m`. O X permite variáveis externas, desde que elas sejam
> conhecidas no momento da previsão ou sejam usadas com atraso causal.
>
> Testamos ordens candidatas no treino, usando critério de informação, e
> avaliamos um passo à frente no período de teste. O modelo tem reajustes
> periódicos, cujo custo computacional é maior que uma previsão com RF ou MLP
> já treinados. Nos grupos horários, mantivemos a grade temporal; não
> comprimimos as horas sem alvo como se o tempo tivesse deixado de passar.
>
> Nos MAEs da comparação, SARIMAX foi o melhor dos quatro em Bitcoin, com
> 1.391,90, e no ouro, com 19,51. No tráfego obteve 351,88 e no clima 0,4122,
> atrás dos líderes. Na poluição, o MAE foi 32,22, muito pior que os demais;
> isso mostra que uma estrutura estatística mais elaborada não garante bom
> desempenho em toda série.

**Ressalvas indispensáveis:** no clima, 0,4122 é o MAE salvo no notebook para
13.785 datas oficiais. A reprodução independente encontrou 0,4118, sem mudar
a posição. Falta registrar no notebook a lista datada das previsões para que
o comparador automático audite esse quinto grupo. O ajuste também emitiu
avisos de convergência. Na poluição, o desempenho ruim precisa ser reconhecido;
não usem o MAE antigo calculado em outro subconjunto de datas.

**Passagem:** “A seguir, Martins apresenta o modelo de árvores e mostra como
transformamos a série em atributos sem usar informação do futuro.”

## 4. Martins — Random Forest e features

**HTML:** 04 Modelos → aba **Random Forest**; depois, 05 Resultados → botões
**Tráfego** e **Poluição**.

**Fala sugerida:**

> A Random Forest combina muitas árvores de decisão. Para aplicá-la a uma
> série temporal, criamos uma tabela supervisionada: atrasos do alvo e das
> variáveis externas, estatísticas móveis e informações de calendário. O
> cuidado principal é que cada linha só pode conter o que estaria disponível
> antes da hora, dia ou semana que queremos prever. Uma média móvel que inclui
> o alvo futuro seria vazamento e melhoraria artificialmente o teste.
>
> Fizemos busca aleatória de doze configurações em três janelas temporais
> expansivas dentro do treino. Testamos parâmetros como número de árvores,
> profundidade, mínimo de amostras para divisão e quantidade de features. O
> menor MAE de validação definiu a configuração. No teste, a floresta ficou
> congelada; atualizamos as entradas em cada origem de um passo.
>
> A Random Forest venceu no tráfego, com MAE 153,29, e na poluição, com
> 9,87. No clima obteve 0,3951, perto da MLP. Em Bitcoin e ouro, os MAEs foram
> 1.661,42 e 36,16. Árvores não extrapolam facilmente um novo patamar de
> preço além do observado no treino, o que ajuda a explicar a dificuldade
> nessas duas séries.

**Sobre importância das features:** os notebooks calculam importância por
permutação com a função compartilhada `calcular_importancia_features`.
Embaralha-se uma entrada de cada vez e mede-se quanto o MAE piora. Uma
importância pequena não prova que a variável é inútil: lags correlacionados
podem dividir o mesmo sinal. Se exibirem um gráfico do notebook, leiam os
nomes e números reais daquele grupo; o HTML não contém esse gráfico.

**Sobre cobertura:** nas datas da comparação, RF cobre 10.267 de 10.511
instantes do teste de tráfego e 6.336 de 7.013 na poluição. Perfis reduzidos
de features foram experimentados para prever instantes adicionais, mas não
substituem automaticamente as origens oficiais do ranking.

**Passagem:** “O Dmitri fecha os modelos com a rede neural, que também usa
features temporais, mas aprende relações contínuas entre elas.”

## 5. Dmitri — MLP Regressor

**HTML:** 04 Modelos → aba **MLP Regressor**; depois, 05 Resultados → **Clima**.

**Fala sugerida:**

> A MLP é uma rede neural de camadas densas. Ela recebe a mesma ideia de
> tabela temporal: lags, janelas, calendário e exógenas disponíveis. As
> camadas combinam essas entradas para aprender relações não lineares, e a
> saída é um valor contínuo previsto. Diferentemente do SARIMAX, a estrutura
> temporal não está embutida na equação; precisamos fornecê-la nas features.
>
> Escalonamos os dados com parâmetros aprendidos somente no treino de cada
> janela. Comparamos cinco arquiteturas compactas em três folds
> cronológicos, escolhendo pelo MAE médio. Uma parte final do treino orienta
> a parada antecipada, para evitar treino excessivo. Depois a rede escolhida
> é ajustada no treino e seus pesos ficam fixos durante o teste.
>
> A MLP venceu no clima com MAE 0,3821 °C, contra 0,3951 do RF e 0,4122
> salvo para SARIMAX. Foi a segunda no Bitcoin, com 1.401,83, e no tráfego,
> com 180,41. Na poluição e no ouro obteve 10,69 e 22,65. Portanto, a rede
> foi competitiva em várias bases, mas não venceu automaticamente por ser
> mais flexível.

**Ressalva indispensável:** os modelos de Bitcoin e ouro foram revisados
depois de olhar o erro no teste. Mesmo que a nova escolha de hiperparâmetros
tenha sido feita em folds de treino, a decisão de revisar foi influenciada
pelo teste. Chamem esses dois resultados de **exploratórios**. Uma afirmação
confirmatória exigiria um novo período de teste ainda não consultado.

**Sobre importância:** a permutação mede a piora do MAE ao embaralhar uma
feature após o ajuste. O resultado mostra associação preditiva para aquele
modelo e período, não causalidade. Se quiserem mostrar os valores, abram a
seção de importância do notebook correspondente.

**Passagem:** “Com os quatro métodos apresentados, voltamos à comparação nas
mesmas datas. A Sofia reúne os resultados e o Felipe conduz a conclusão.”

## 6. Sofia e Felipe — comparação, cobertura e conclusão

**HTML:** 05 Resultados, 06 Cobertura, 07 Conclusão. Felipe pode clicar
sequencialmente em cada base; Sofia lê a ordem e explica o significado.

| Base | 1º | 2º | 3º | 4º | Datas comuns / teste |
|---|---|---|---|---|---|
| Bitcoin | SARIMAX 1.391,90 | MLP 1.401,83 | Holt-Winters 1.404,19 | RF 1.661,42 | 884 / 884 |
| Tráfego | RF 153,29 | MLP 180,41 | Holt-Winters 332,70 | SARIMAX 351,88 | 10.267 / 10.511 |
| Poluição | RF 9,87 | Holt-Winters 10,39 | MLP 10,69 | SARIMAX 32,22 | 6.336 / 7.013 |
| Clima* | MLP 0,3821 | RF 0,3951 | SARIMAX 0,4122 | Holt-Winters 0,6866 | 13.785 / 14.026 |
| Ouro | SARIMAX 19,51 | Holt-Winters 19,57 | MLP 22,65 | RF 36,16 | 601 / 601 |

\* No clima, a posição do SARIMAX usa o MAE salvo e as datas oficiais
conferidas. A série datada ainda precisa ser incorporada ao notebook para
completar a auditoria automática. A reprodução independente encontrou 0,4118,
sem alterar a posição.

**Fala sugerida para Sofia:**

> O ranking compara os quatro modelos apenas nas mesmas observações de cada
> base. SARIMAX venceu em Bitcoin e ouro; RF venceu em tráfego e poluição; MLP
> venceu em clima. Holt-Winters não venceu, mas ficou próximo do líder em
> Bitcoin e ouro. Em número de vitórias, são 2 para SARIMAX, 2 para RF, 1 para
> MLP e 0 para Holt-Winters. A posição média ordinal é 2,6; 2,4; 2,2; e 2,8,
> respectivamente. Isso não substitui a análise por base: a série determina
> qual hipótese de modelo funciona melhor.
>
> A cobertura das datas comuns é 100% em Bitcoin e ouro, 97,68% em tráfego,
> 90,35% em poluição e 98,28% em clima, em relação ao teste oficial. Esses
> percentuais dizem quantas origens puderam entrar na comparação; não dizem
> sozinhos que o modelo é bom. Nas seções de resíduos, autocorrelação remanescente
> indica que ainda há padrão temporal não capturado.

**Fechamento sugerido para Felipe:**

> A principal conclusão é que não há um vencedor universal. O projeto entrega
> um protocolo temporal comum, cinco bases tratadas, vinte experimentos e uma
> comparação por datas equivalentes. Há três cuidados ao interpretar a nota
> final: diferenças muito pequenas ainda não têm teste formal de significância;
> a auditoria datada do SARIMAX no clima precisa ser concluída; e os MLPs de
> Bitcoin e ouro tiveram revisão orientada por uma inspeção do teste. Esses
> limites estão documentados. O próximo passo seria confirmar diferenças
> pequenas em um novo período e melhorar os casos em que restam padrões nos
> resíduos.

## Perguntas prováveis da banca

**“Por que não comparar o MAE total das cinco bases?”** Porque os alvos têm
unidades e escalas diferentes. O MAE só ordena modelos dentro da mesma base.

**“É walk-forward se RF e MLP não são reajustados a cada previsão?”** Sim: a
origem e as entradas avançam no tempo. A política de reajuste é uma decisão
separada. RF e MLP usam pesos fixos no teste; os modelos estatísticos atualizam
estado ou fazem reajustes conforme sua implementação.

**“Por que o teste não começa no mesmo instante para os quatro modelos?”**
Algumas origens não têm alvo ou histórico suficiente para construir as
features. Por isso são informadas a cobertura e a interseção das datas, e o
ranking usa somente os instantes em que todos previram.

**“O menor MAE prova que o modelo é superior?”** Prova apenas menor erro
observado naquele recorte. Diferenças pequenas, como em Bitcoin, clima e ouro,
precisam de análise de incerteza ou outro período de teste antes de uma
conclusão forte.

**“Por que o SARIMAX foi tão ruim na poluição?”** A configuração avaliada teve
MAE 32,22 nas datas comuns, muito acima dos demais. O resultado deve ser
investigado com resíduos, convergência, exógenas e especificação; não há base
para afirmar uma causa única apenas a partir do MAE.

**“Onde estão as evidências?”** Os notebooks `grupoN/modelo-N.ipynb` contêm
buscas, gráficos, métricas e previsões. `comparacao-20-modelos.ipynb` audita as
previsões datadas de quatro bases e aponta a pendência do SARIMAX no clima.
`GUIA_PRODUCAO_E_STATUS.md` registra a produção das bases e as limitações.
