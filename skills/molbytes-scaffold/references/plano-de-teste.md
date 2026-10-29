# Plano de teste

O estágio 8 parte de um plano: a lista do que precisa ser verificado, ligada à
origem de cada item. O plano é executado, cada item é marcado, as falhas são
corrigidas automaticamente e o plano roda de novo. O estágio 11 roda o plano
inteiro outra vez antes do gate.

## 8.1 Gerar o plano (scaffold-tester)

`.project/plano-de-teste.yaml`, a partir de: critérios de aceite de
`tickets.yaml`, fluxos de `design/user-flows.md` (sem design, os da spec),
riscos altos do MVP em `risks.yaml` e `security_requirements`. Todo critério
de aceite e todo `security_requirements` aparece em pelo menos um item.

```yaml
itens:
  - id: TP-001
    titulo: Pedido com PIX confirma após webhook assinado
    origem: [BE-004, FLUXO-checkout, SR-003]   # ticket, fluxo, risco ou requisito
    tipo: automatizado      # automatizado | manual
    teste: tests/integration/test_pix.py::test_webhook_assinado   # onde está o teste
    status: pendente        # pendente | passou | falhou | bloqueado | manual | aceito
    tentativas: 0
    detalhe: ""             # motivo da falha, do bloqueio ou do aceite
```

- `manual`: só o que não dá para automatizar (impressora, leitor de código de
  barras, aparência visual, e-mail real, hardware). Diga por que no `detalhe`.
- Premissa sobre terceiros ainda aberta (spec, `sondagens.md`): um item
  `manual` "Confirmar P-0X na conta de teste" (ou com o suporte, ou com a
  pessoa), com o que muda se ela for negada.
- Modo alteração: inclua a regressão das áreas tocadas; teste que já falhava
  no ponto de partida recebe `status: aceito`, `detalhe: já falhava antes da
  alteração`.

Mostre ao usuário só o resumo (total de itens, quantos automatizados e
quantos manuais, origens sem item) e siga, sem pausa.

## 8.2 Executar e marcar (scaffold-tester)

Escreva os testes automatizados que faltam, rode a suíte e marque cada item
com o resultado real:

- `passou` / `falhou` (com a mensagem de erro resumida em `detalhe`);
- `bloqueado`: falha de **ambiente**, não de código (Docker parado, porta
  ocupada, serviço externo fora). Não vai para correção: resolva o ambiente ou
  informe o usuário.

## Trava dos testes (fim do 8.2)

Depois de marcar o plano, e antes de qualquer correção, trave os testes: a
partir daqui, o que muda é o código, não o teste.

1. Commit `scaffold(8): testes do plano`.
2. Grave `.project/testes-travados.txt`: um caminho por linha, relativo à
   raiz do projeto, de cada arquivo citado em `teste:` de um item
   automatizado (a parte antes de `::`), sem repetir.
3. Grave em `state.md` a linha `Testes travados: <sha>`, com o `HEAD` que o
   próprio git dá (`git rev-parse --short HEAD`), não o que um subagente
   relatar.

**Conferência depois de cada correção** (8.3, 9.3, `FIX-REVIEW`,
`FIX-IMPACTO`, estágio 11, `FIX-MANUAL`): rode você mesmo
`git diff --name-only <Testes travados> -- <caminhos de testes-travados.txt>`.

- Vazio: segue.
- Algum arquivo mudou com o sim do usuário (passo 2 do 8.3): aceite como
  abaixo, sem perguntar de novo.
- Algum arquivo mudou sem o sim: mostre ao usuário o arquivo, o motivo que o
  implementador deu e o diff resumido, e pergunte: **aceitar** (o teste
  estava errado em relação à spec; o motivo vai para o `detalhe` do item e
  `Testes travados:` passa a ser o `HEAD` atual) ou **desfazer**
  (`git checkout <Testes travados> -- <arquivo>`, e o ticket de correção
  volta ao implementador com "o teste não muda").
- Teste novo que uma correção criou (ex.: o de reprodução de um
  `SECURITY-00X`) entra em `testes-travados.txt` quando a correção é aceita,
  e `Testes travados:` passa a ser o `HEAD`.

## 8.3 Corrigir as falhas (automático)

Para cada item `falhou`, um por vez:

1. Escreva o ticket de correção `FIX-TP-00X` (fim de `stages.md`) com o item,
   o teste, a mensagem de erro e o trecho da spec, e lance um
   `scaffold-implementer` com ele. Modelo na 1ª tentativa: o mais alto entre
   os tickets de `origem` em `agent-map.json` (sem ticket na origem, só fluxo,
   risco ou SR: medio); na 2ª, forte.
2. A correção é **no código de produção**. Se o implementador achar que o
   teste está errado em relação à spec, ele não o edita: responde
   `TESTE ERRADO:` com o arquivo e o motivo. Pergunte ao usuário; com o sim,
   relance o implementador com "pode mudar <arquivo>: <motivo>". Isso não
   conta tentativa.
3. Rode de novo o teste do item e os da mesma área. Marque o resultado e some
   1 em `tentativas`.
4. **Máximo de 2 tentativas por item.** Depois disso, pare e pergunte ao
   usuário: tentar outra abordagem, ou aceitar a falha como pendência
   (`status: aceito`, motivo em `detalhe`).

Commit a cada item corrigido: `scaffold(8): fix TP-00X`.

## 8.4 Relatório

`.project/test-report.md`: comandos usados, totais por status, cobertura real
(se a ferramenta medir), itens corrigidos e em quantas tentativas, itens
aceitos com o motivo, e a lista **"Testes manuais a fazer"** (itens `manual`,
com o passo a passo para a pessoa executar). A lista começa por **"Preparar o
ambiente"**: migrações a aplicar, dados de exemplo, variáveis e chaves de
configuração, contas de teste; depois, as premissas abertas, que são as que
mais podem mudar o código. Só números que a ferramenta mostrou.

## Estágio 11

O `scaffold-tester` roda o plano inteiro de novo (os estágios 9 e 10 mudam
código). Atualize os
status. O tester não muda teste travado: teste que ele acha errado vai para
o `detalhe` e para você, como na conferência da trava. Falha nova passa pelo mesmo ciclo do 8.3. O gate exige todo item
automatizado `passou` ou `aceito`. Itens `manual` não bloqueiam: vão para o
`pipeline-report.md` em "Testes manuais a fazer".
