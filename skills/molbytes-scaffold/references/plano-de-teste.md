# Plano de teste

O estágio 8 parte de um plano: a lista do que precisa ser verificado, ligada à
origem de cada item. O plano é executado, cada item é marcado, as falhas são
corrigidas automaticamente e o plano roda de novo. O estágio 11 roda o plano
inteiro outra vez antes do gate.

## 8.1 Gerar o plano (scaffold-tester)

`.project/plano-de-teste.yaml`, a partir de: critérios de aceite de
`tickets.yaml`, fluxos de `design/user-flows.md`, riscos altos do MVP em
`risks.yaml` e `security_requirements`. Todo critério de aceite e todo
`security_requirements` aparece em pelo menos um item.

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

## 8.3 Corrigir as falhas (automático)

Para cada item `falhou`, um por vez:

1. Lance um `scaffold-implementer` com: o item, o teste, a mensagem de erro, o
   trecho da spec e o ticket de origem. Modelo: o do ticket de origem em
   `agent-map.json` na 1ª tentativa; opus na 2ª.
2. A correção é **no código de produção**. O teste só pode mudar se estiver
   errado em relação à spec; nesse caso o implementador explica o motivo, que
   vai para o `detalhe`, e o reviewer confere no estágio 10.
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
com o passo a passo para a pessoa executar). Só números que a ferramenta
mostrou.

## Estágio 11

Rode o plano inteiro de novo (os estágios 9 e 10 mudam código). Atualize os
status. Falha nova passa pelo mesmo ciclo do 8.3. O gate exige todo item
automatizado `passou` ou `aceito`. Itens `manual` não bloqueiam: vão para o
`pipeline-report.md` em "Testes manuais a fazer".
