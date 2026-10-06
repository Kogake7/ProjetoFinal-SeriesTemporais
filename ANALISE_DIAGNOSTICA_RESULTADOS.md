# Análise diagnóstica dos cinco grupos e dos 20 modelos

Leitura das saídas salvas em 6 de outubro de 2026. Este texto interpreta os
experimentos existentes; **não representa um novo ajuste dos modelos**. Para
conferir os resíduos de forma uniforme, recalculei erro assinado, dispersão,
ACF e Ljung-Box a partir das previsões datadas salvas nos notebooks de 19
combinações. No SARIMAX 4, a série datada ainda não foi salva: uso as métricas e
o diagnóstico exibidos no próprio notebook e marco essa limitação.

## Resumo que vale apresentar

1. **Tráfego e clima são os casos de maior ganho prático.** No tráfego, RF
   reduz o MAE da persistência de 590,79 para 153,29 (74,05%). No clima,
   MLP reduz de 0,6865 para 0,3821 °C (44,35%).
2. **Poluição tem ganho modesto.** RF vence entre os quatro modelos e melhora
   5,04% sobre persistência. Holt-Winters praticamente empata com ela; MLP
   fica um pouco pior; o SARIMAX oficial tem erro e viés elevados.
3. **Em Bitcoin e ouro, ganhar entre os quatro modelos não implica ganhar de
   uma regra simples.** SARIMAX lidera os modelos em ambos, mas no Bitcoin
   fica 0,36% pior que persistência. No ouro melhora apenas 0,32%; a diferença
   é pequena demais para afirmar superioridade robusta sem análise pareada.
4. **MAE baixo não implica resíduos independentes.** Quase todos os modelos
   horários mantêm autocorrelação detectável. Isso indica estrutura remanescente
   e sugere caminhos de melhoria, mesmo quando o modelo já é útil.
5. **Quatro rankings têm auditoria automática integral das previsões datadas.**
   No clima, o SARIMAX tem MAE salvo de 0,4122 nas 13.785 datas oficiais; uma
   reprodução independente encontrou 0,4118. A ordem dos modelos não muda,
   mas sua série datada ainda precisa ser gravada para completar a auditoria.

## Como ler os diagnósticos

- **MAE** é a média de `|real - previsto|` na unidade original de cada base.
  **ME/viés** é a média de `real - previsto`: positivo indica subestimação;
  negativo, superestimação. Um ME próximo de zero pode esconder erros positivos
  e negativos grandes que se anulam.
- **Persistência** prevê o último valor observado. Ela é uma referência externa
  ao ranking dos quatro modelos e foi calculada nas mesmas datas. Em séries de
  preço, seu desempenho é especialmente importante para avaliar utilidade.
- **ACF** mede a relação do erro com erros passados. **Ljung-Box** testa a
  hipótese conjunta de ausência de autocorrelação até um lag escolhido.
  `p < 0,05` rejeita essa hipótese; não mede o tamanho do erro e não prova
  que todo lag individual seja relevante. `p >= 0,05` significa ausência de
  evidência de autocorrelação nesse teste, não prova de ruído branco perfeito.
- Para preservar o significado de “1 hora”, “1 dia” ou “1 semana”, recalculei
  ACF/Ljung-Box no **maior trecho sem lacunas do teste**. As previsões fora
  desse trecho continuam no MAE, no viés e na cobertura. Tamanho do trecho:
  Bitcoin 884, tráfego 1.420, poluição 626, clima 12.404 e ouro 601. Com
  muitos dados, até dependências pequenas podem gerar p-valores muito baixos;
  por isso os coeficientes de ACF e o MAE também devem ser considerados.
- **Resíduo da decomposição STL não é erro de previsão.** A STL usa a série de
  treino para separar tendência, sazonalidade e resto; seu Ljung-Box não
  substitui o Ljung-Box das previsões fora da amostra.
- Os blocos T17 antigos de Holt-Winters pertencem ao estudo **multipasso**.
  Os T17 antigos de SARIMAX 2 e 3 pertencem à análise anterior em outra
  cobertura. As conclusões abaixo usam as previsões oficiais **de um passo**.

## Qualidade das bases: o que os testes iniciais mostraram

O `manifesto.json` documenta a regularização temporal antes da modelagem.
Contagens abaixo são da **grade completa**, não apenas do teste:

| Base | Linhas da grade | Alvos observados | Alvos ausentes | Ocorrências relevantes na fonte |
|---|---:|---:|---:|---|
| Bitcoin | 2.945 | 2.922 | 23 | 23 dias sem timestamp na fonte. |
| Tráfego | 52.551 | 40.575 | 11.976 | 17 duplicatas exatas e 7.612 timestamps repetidos após deduplicação exata. |
| Poluição | 35.064 | 34.139 | 925 | Há lacunas de PM2.5, preservadas como ausência do alvo. |
| Clima | 70.129 | 70.041 | 88 | 327 duplicatas exatas e 38 sentinelas `-9999`. |
| Ouro | 2.402 | 2.402 | 0 | Série adaptada para frequência semanal. |

O tratamento colocou os dados em uma grade regular, resolveu duplicatas e
sentinelas, e preencheu algumas **exógenas** apenas a partir de medições
anteriores, com limite. O alvo não foi imputado. Isso evita fabricar acertos
nas horas/dias sem valor real e explica parte das origens inelegíveis. A base
bruta de tráfego, por exemplo, não deve ser descrita como “horária completa”
apenas porque o Excel final tem uma linha para cada hora.

## Dados e decomposição: o que se pode concluir

| Base | Força de tendência STL | Força sazonal STL | Leitura útil |
|---|---:|---:|---|
| Bitcoin | 0,9933 | 0,0000, ciclo de 7 dias | Mudança de nível domina; não há evidência de sazonalidade semanal estável nesse recorte de treino. |
| Tráfego | 0,0898 | 0,7665, ciclo de 24 horas | Ciclo diário forte; hora do dia e histórico diário/semanal são candidatos naturais. |
| Poluição | 0,8209 | 0,0275, ciclo de 24 horas | Tendência importante no trecho analisado e ciclo diário fraco; a dinâmica recente e exógenas podem importar mais. |
| Clima | 0,9579 | 0,6910, ciclo de 24 horas | Há tendência e ciclo diário; testar lags de temperatura e calendário horário é coerente. |
| Ouro | 0,9574 | 0,0000, ciclo de 52 semanas | Mudança de nível domina; a sazonalidade anual semanal não ajudou no recorte de treino. |

Essas forças foram calculadas em trechos de treino mostrados nos notebooks,
alguns deles menores que o histórico completo. São diagnósticos descritivos do
trecho escolhido, não características imutáveis da base. O resíduo STL rejeita
ausência de autocorrelação nas cinco séries; portanto a decomposição sozinha
não capturou toda a dinâmica.

## Resultado de teste e comparação com persistência

Todos os MAEs abaixo referem-se a **um passo e às datas comuns dentro da
respectiva base**. Não comparem o valor numérico entre linhas de bases
diferentes. `+` significa melhora de MAE sobre a persistência; `−`, piora.

| Base | Datas comuns / grade | Persistência | SARIMAX | Holt-Winters | Random Forest | MLP |
|---|---:|---:|---:|---:|---:|---:|
| Bitcoin | 884 / 884 | 1.386,96 | 1.391,90 (−0,36%) | 1.404,19 (−1,24%) | 1.661,42 (−19,79%) | 1.401,83 (−1,07%) |
| Tráfego | 10.267 / 10.511 | 590,79 | 351,88 (+40,44%) | 332,70 (+43,69%) | 153,29 (+74,05%) | 180,41 (+69,46%) |
| Poluição | 6.336 / 7.013 | 10,3906 | 32,2177 (−210,07%) | 10,3912 (≈0%) | 9,8670 (+5,04%) | 10,6862 (−2,84%) |
| Clima* | 13.785 / 14.026 | 0,6865 | 0,4122 (+39,96%) | 0,6866 (≈0%) | 0,3951 (+42,45%) | 0,3821 (+44,35%) |
| Ouro | 601 / 601 | 19,5735 | 19,5104 (+0,32%) | 19,5735 (≈0%) | 36,1629 (−84,75%) | 22,6521 (−15,73%) |

\* Clima: valor salvo do SARIMAX. A reprodução independente encontrou 0,4118,
o que mantém a terceira colocação.

### Busca e validação: interpretação correta

- RF testou 12 configurações em três janelas temporais expansivas, escolhendo
  pelo MAE de validação. A floresta selecionada fica fixa no teste; as entradas
  são atualizadas em cada origem. A busca não garante ótimo global.
- MLP comparou cinco arquiteturas em três folds temporais, com escala ajustada
  no treino de cada janela e parada antecipada. Os MLPs de Bitcoin e ouro foram
  **revisados após inspeção do teste**; seus resultados atuais são
  exploratórios, mesmo com a nova busca feita dentro do treino.
- Holt-Winters selecionou a versão oficial de um passo no treino: tendência
  no Bitcoin, tendência com sazonalidade no tráfego, e nível nas outras três
  bases. Os ajustes finais declararam convergência. Os resultados multipasso
  anteriores respondem a outra pergunta e não devem ser somados ao ranking.
- SARIMAX 2 e 3 têm uma avaliação oficial corrigida na grade horária completa.
  No SARIMAX 3, os dois candidatos de validação registraram **não
  convergência**; o ajuste final declarou convergência, mas o MAE saltou de
  cerca de 12,3 na validação para 32,22 no teste. Isso pede revisão da
  estabilidade e da calibração. O SARIMAX 4 teve avisos de não convergência.

### Ensaios de cobertura do Random Forest

Os grupos 2 e 3 também testaram perfis com menos lags/janelas para alcançar
mais horários. São **experimentos adicionais**, fora do ranking T16 atual.
No tráfego, remover o lag 168 levou o teste a 10.296 horas (97,95% da grade)
com MAE 151,24; o perfil atual usa 10.267 horas (97,68%) e MAE 153,29.
Nas 10.267 datas comuns, o perfil sem lag 168 marcou 151,44, então o ganho
observado não decorre somente das 29 horas adicionais.
Na poluição, o perfil reduzido com nova busca própria de hiperparâmetros
chegou a 6.770 horas (96,54%) e MAE 9,74, contra 6.336 horas (90,35%) e
9,87 do perfil oficial. **Não comparar 9,74 diretamente com 9,87 como se
fossem os mesmos instantes**: nas 6.336 datas comuns, o perfil reduzido
obteve 9,80 contra 9,87. Os 434 horários adicionais tiveram MAE 8,83.
Esses resultados sugerem um caminho para ampliar cobertura, mas só entram
na comparação dos quatro modelos depois de alinhar novamente as datas de
todos eles e definir o perfil sem escolher com base no teste.

## Resíduos oficiais: diagnóstico comparável

Cada linha usa `real − previsto` de um passo. `ACF(1)` é a autocorrelação no
primeiro lag do maior trecho contínuo. `p LB` é o p-valor de Ljung-Box **até**
o lag indicado (7 dias, 24 horas ou 52 semanas), portanto não prova que a
dependência esteja exatamente nesse lag. `≈0` indica valor que arredondou ou
subfluiu para zero na saída. No clima, a linha SARIMAX vem da saída salva.

| Base | Modelo | ME/viés | ACF(1) | p LB até o lag indicado | Leitura |
|---|---|---:|---:|---:|---|
| Bitcoin | SARIMAX | −6,17 | −0,008 | 0,863 (7) | Sem rejeição nos lags avaliados; viés médio pequeno. |
| Bitcoin | Holt-Winters | −20,19 | 0,087 | 0,232 (7) | O lag 1 isolado rejeita (p=0,0099); não chamar de ruído branco. |
| Bitcoin | RF | +943,56 | 0,027 | 0,194 (7) | Pouca autocorrelação detectada, mas subestima fortemente o nível. |
| Bitcoin | MLP | +160,48 | −0,032 | 0,600 (7) | Sem rejeição nos lags avaliados; ainda pior que persistência no MAE. |
| Tráfego | SARIMAX | −99,95 | 0,481 | <10⁻¹⁴³ (24) | Superestima em média e mantém forte dependência de curto prazo. |
| Tráfego | Holt-Winters | +0,93 | 0,456 | <10⁻¹⁹⁴ (24) | Viés global pequeno, mas erros consecutivos se parecem. |
| Tráfego | RF | +0,99 | 0,195 | <10⁻²⁷ (24) | Menor MAE e pouco viés, porém ainda há padrão temporal residual. |
| Tráfego | MLP | +28,66 | 0,035 | <10⁻¹⁵ (24) | Lag 1 não rejeita (p≈0,188), mas o teste conjunto até 24 rejeita. |
| Poluição | SARIMAX | −30,26 | 0,160 | 0,0127 (24) | Superestimação sistemática: média prevista 111,52 contra real 81,27. |
| Poluição | Holt-Winters | +0,01 | 0,381 | <10⁻¹⁵ (24) | Quase sem viés, mas não melhora a persistência e mantém dependência. |
| Poluição | RF | +0,21 | 0,198 | 0,0295 (24) | Ganho pequeno e autocorrelação remanescente. |
| Poluição | MLP | +1,51 | 0,213 | <10⁻¹¹ (24) | Erro um pouco acima da persistência; há dependência residual. |
| Clima* | SARIMAX | +0,003 | — | <10⁻¹⁵⁶ (24) | MAE competitivo, mas diagnóstico datado não foi refeito. |
| Clima | Holt-Winters | −0,001 | 0,714 | ≈0 (24) | Quase igual à persistência; muita estrutura temporal permanece. |
| Clima | RF | +0,022 | 0,095 | <10⁻⁴² (24) | Erro baixo, viés pequeno, mas não independente. |
| Clima | MLP | +0,050 | 0,028 | <10⁻³³ (24) | Menor MAE; dependência pequena no lag 1, porém detectável no conjunto. |
| Ouro | SARIMAX | +1,28 | −0,009 | 0,000040 (52) | Quase sem relação no lag 1; há dependência em algum lag até 52. |
| Ouro | Holt-Winters | +1,66 | −0,009 | 0,000040 (52) | Praticamente a persistência; ainda há dependência em lags maiores. |
| Ouro | RF | +31,39 | 0,418 | ≈0 (52) | Subestima e acumula erros persistentes. |
| Ouro | MLP | +12,14 | 0,051 | <10⁻¹⁵ (52) | Subestima e perde para persistência, apesar de lag 1 fraco. |

Não se deve dizer “há sazonalidade residual de 52 semanas” apenas porque o
Ljung-Box até o lag 52 rejeitou. Esse teste soma a evidência de todos os lags
intermediários. Para localizar um ciclo, é necessário olhar a ACF, o espectro
e repetir a análise em períodos diferentes.

## Leitura por base e conclusão que pode ser usada no relatório

### 1. Bitcoin

**Resultado:** SARIMAX tem o menor MAE entre os quatro (1.391,90), mas a
persistência tem 1.386,96. A diferença entre SARIMAX, MLP e Holt-Winters é
pequena diante dos erros absolutos diários. O R² alto dos modelos de nível
também aparece na persistência; ele não demonstra ganho incremental.

**Diagnóstico:** STL aponta tendência muito forte e força sazonal semanal
nula. SARIMAX, RF e MLP não rejeitam ausência de autocorrelação nos lags
avaliados do erro de teste. Isso é compatível com uma série cujo próximo
movimento é difícil de antecipar. RF tem viés de +943,56, sinal de
subestimação do nível, coerente com a dificuldade de árvores em extrapolar
patamares novos. O lag do alvo é a feature dominante no RF. Holt-Winters
mostra pequena dependência no lag 1.

**Frase defensável:** “Entre os quatro, SARIMAX foi o melhor, mas nenhum
mostrou ganho de MAE sobre repetir o último preço; a utilidade adicional
permanece não demonstrada neste teste.”

### 2. Tráfego

**Resultado:** RF vence com 153,29; MLP vem depois com 180,41; os dois
superam amplamente a persistência de 590,79. Holt-Winters e SARIMAX também
melhoram a referência, mas são bem menos precisos que os modelos de tabela.

**Diagnóstico:** a força sazonal diária STL é 0,7665. Importâncias do RF e
MLP destacam volume na hora anterior, hora do dia, lag 24 e lag 168: há
memória curta e ciclos diários/semanais úteis. RF tem viés próximo de zero;
SARIMAX oficial superestima em média cerca de 100 veículos/h. Todos rejeitam
o Ljung-Box até 24 horas. No MLP, o lag 1 sozinho não rejeita, mas o teste
conjunto rejeita, indicando que olhar só uma defasagem seria insuficiente.

**Frase defensável:** “O calendário e o histórico tornam a previsão de
tráfego muito melhor que a persistência, mas os resíduos ainda sugerem
ocasiões ou padrões não capturados.”

### 3. Poluição

**Resultado:** RF vence com MAE 9,87 e ganho de 5,04% sobre persistência.
Holt-Winters praticamente empata com a regra ingênua e MLP fica 2,84% pior.
SARIMAX oficial tem MAE 32,22, mais de três vezes o da persistência.

**Diagnóstico:** o ciclo diário STL é fraco (0,0275). No RF, lag 1 do PM2.5
domina a importância; PM10 e vento aparecem com contribuição adicional.
No MLP, ponto de orvalho e temperatura também têm importância por
permutação. Em todos os modelos há autocorrelação residual, embora o RF
reduza a ACF(1) em relação a Holt-Winters. O SARIMAX apresenta ME −30,26,
ou seja, previsão média 111,52 para valor real médio 81,27. O MAE dele
aumenta de 29,61 na primeira metade para 34,83 na segunda. A causa exata
exige investigar especificação, escala, parâmetros e mudança temporal;
o viés por si só não identifica uma única causa.

**Frase defensável:** “RF traz uma melhora real, mas pequena. O SARIMAX
precisa de recalibração antes de ser uma opção para esta base.”

### 4. Clima

**Resultado:** MLP vence com 0,3821 °C; RF tem 0,3951; SARIMAX salvo,
0,4122; Holt-Winters, 0,6866, praticamente igual à persistência 0,6865.
MLP e RF reduzem bastante o erro da regra simples. A diferença entre MLP e
RF é cerca de 0,013 °C, portanto a ordem observada não demonstra, sozinha,
superioridade estável em outro período.

**Diagnóstico:** STL mostra tendência e ciclo diário fortes. Lag 1 de
temperatura domina a importância por permutação de RF e MLP; hora do dia e
lags adicionais contribuem. MLP tem ACF(1) 0,028, RF 0,095 e
Holt-Winters 0,714 no maior trecho contínuo. O Ljung-Box conjunto rejeita
em todos; o modelo mais preciso ainda pode ser melhorado. O SARIMAX apresenta
avisos de não convergência e falta a série datada para auditoria completa.

**Frase defensável:** “MLP teve o menor MAE no teste, seguida de perto por
RF. É uma vitória observada, ainda sem teste pareado de incerteza, e o
terceiro lugar do SARIMAX é provisório quanto à reprodução datada.”

### 5. Ouro

**Resultado:** SARIMAX é primeiro entre os quatro com 19,5104, mas a
persistência tem 19,5735: ganho de apenas 0,32%. Holt-Winters coincide com
a referência. RF (36,16) e MLP (22,65) ficam piores.

**Diagnóstico:** STL não encontrou sazonalidade anual de 52 semanas no
trecho analisado. O erro de todos cresce na segunda metade: SARIMAX 10,96
→ 28,03; Holt-Winters 11,01 → 28,11; MLP 12,17 → 33,10; RF 17,26 →
55,00. Isso mostra que a dificuldade muda ao longo do teste; a hipótese de
mudança de regime/escala é plausível, mas não está provada por essa divisão.
RF tem viés de +31,39 e ACF(1) 0,418, compatível com subestimação
persistente em patamares acima dos que aprendeu. SARIMAX e Holt-Winters têm
erros muito parecidos com a persistência.

**Frase defensável:** “A pequena vitória do SARIMAX sobre a persistência
não justifica declarar uma vantagem robusta; os modelos de árvores e rede
sofrem especialmente na parte final do teste.”

## Importância de features: o que afirmar e o que evitar

As tabelas do RF e da MLP usam **importância por permutação**: embaralhar
uma feature aumenta o MAE em certa quantidade. Isso mede dependência do
modelo avaliado naquela amostra, não efeito causal. Features correlacionadas
podem dividir importância ou mascarar umas às outras. Uma importância
pequena não é justificativa suficiente para remover um lag antes de testar
a cobertura e o MAE resultantes.

No SARIMAX, a tabela de coeficientes e o teste de permutação tratam das
**exógenas**; os termos AR/MA não entram nessa ordenação. Alguns testes de
permutação usam apenas o **último bloco**, portanto não representam
automaticamente todo o teste. Os p-valores dos coeficientes do SARIMAX 4
são particularmente frágeis diante de avisos de não convergência.

**Leituras mais sólidas:** lag 1 do alvo domina RF nas cinco bases; no
tráfego, calendário horário e lags de 24/168 horas acrescentam informação;
na poluição, PM10/vento entram após o PM2.5 recente; no clima, hora do dia
aparece junto com a temperatura recente. Em Bitcoin e ouro, a forte
dependência de lag 1 não se traduziu em ganho convincente sobre persistência.

## Prioridades para concluir o diagnóstico

1. Salvar as previsões datadas do SARIMAX 4 e repetir a auditoria T16;
   investigar a divergência 0,4118 versus 0,4122 e a convergência do ajuste.
2. Investigar o viés do SARIMAX 3 e validar qualquer correção em período
   ainda não usado para escolher a revisão.
3. Aplicar comparação **pareada das perdas por data**, com incerteza que
   respeite dependência temporal, às diferenças pequenas: SARIMAX versus
   persistência em Bitcoin/ouro e MLP versus RF no clima.
4. Se a conclusão sobre MLP em Bitcoin/ouro precisar ser confirmatória,
   separar um novo período intocado; as versões atuais são exploratórias.
5. Se forem discutir resíduos no relatório, usar apenas os diagnósticos
   oficiais de um passo. Mostrar também viés, dispersão, ACF e cobertura;
   não resumir qualidade do modelo a um único p-valor.

## Se houver pouco tempo na apresentação: seis evidências fortes

| Evidência a mostrar | Conclusão segura em uma frase |
|---|---|
| STL de tráfego e Bitcoin | O tráfego tem ciclo diário forte; Bitcoin mostra tendência e quase nenhuma sazonalidade semanal no treino analisado. |
| Tabela de MAE de tráfego | RF e MLP reduzem muito o erro da persistência no mesmo conjunto de 10.267 horas. |
| Tabela de MAE de Bitcoin e ouro com persistência | Vencer os outros três modelos não basta: o SARIMAX não supera a persistência no Bitcoin e ganha só 0,32% no ouro. |
| Série e ACF dos resíduos de tráfego | Mesmo com MAE baixo, RF mantém autocorrelação; há espaço para capturar mais dinâmica. |
| Viés e erro do SARIMAX em poluição | A superestimação média de 30,26 unidades é um problema de calibração que a ordenação por MAE sozinha não explica. |
| Importância por permutação em clima ou tráfego | O valor recente do alvo domina, e hora/defasagens sazonais acrescentam sinal; importância não equivale a causalidade. |

Para mostrar dispersão de erro, usem o gráfico de resíduos no tempo e o
histograma do mesmo **teste oficial de um passo**. Para comparar dois modelos,
mostrem o erro absoluto nas **mesmas datas**. Para julgar se uma vitória
pequena é robusta, o passo seguinte é analisar a diferença pareada de perdas,
e não repetir o Ljung-Box em cada modelo.

## Onde conferir cada evidência

- `comparacao-20-modelos.ipynb`: MAEs por data comum, cobertura e pendência
  do SARIMAX 4.
- `grupoN/modelo-N.ipynb`: buscas, gráficos, MAE/RMSE/R², resíduos e
  importância de features. Nos notebooks Holt-Winters, a seção oficial de
  um passo está **no fim**; nos SARIMAX 2 e 3, a seção oficial corrigida está
  **depois** do estudo anterior.
- `t08_walk_forward.ipynb`, `walk_forward.py` e `dados_tratados/manifesto.json`:
  cortes e origens oficiais. `GUIA_PRODUCAO_E_STATUS.md` explica a produção
  das bases e limitações da comparação.
