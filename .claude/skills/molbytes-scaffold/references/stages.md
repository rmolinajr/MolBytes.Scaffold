# Estágios em detalhe

## 1. grill-me (sessão principal)

Entreviste o usuário sobre o projeto. Uma pergunta por vez, no máximo 8.
Cubra: usuários e papéis, fluxos principais, stack (se ele já tiver preferência),
restrições (offline, pagamentos, LGPD/RGPD, países), integrações, prazo e o que
fica fora do MVP. Não pergunte o que já está na descrição.

Salve em `.project/qa.json`:
```json
{ "descricao": "...", "respostas": [{"pergunta": "...", "resposta": "..."}],
  "stack": {}, "fora_do_mvp": [] }
```

## 2. to-spec → scaffold-architect (pausa)

Peça ao architect para gerar `.project/spec.md` a partir de `qa.json`, com:
visão geral, arquitetura, modelos de dados, endpoints/contratos, fluxos de
usuário, requisitos não funcionais, fora do escopo, e a seção
**"Segurança e dados pessoais"** descrita em `references/security.md` (parte A).

Depois: mostre um resumo de 10 linhas, peça ao usuário para revisar o arquivo e
**espere a aprovação explícita** antes de continuar. Se ele pedir mudanças,
reenvie ao architect com as mudanças.

## 3. risks-tech-debt → scaffold-architect

Gere `.project/risks.yaml`:
```yaml
risks:
  - id: RISK-001
    titulo: ...
    severidade: alta|media|baixa
    mitigacao: ...
    quando: mvp|v2
tech_debt:
  - id: TD-001
    titulo: ...
    motivo: ...
```
Riscos de severidade alta com `quando: mvp` viram requisitos na etapa 5.

Inclua também a lista `security_requirements` (formato em
`references/security.md`, parte A). Cada requisito precisa ser testável.

## 4. to-design → scaffold-designer

Gere em `.project/design/`: `design-system.md` (cores, tipografia, espaçamento),
`screens.md` (wireframes em texto de cada tela), `user-flows.md`,
`components.md`. Sem Figma: tudo em Markdown.

## 5. to-tickets → scaffold-planner

Gere `.project/tickets.yaml`. Cada ticket:
```yaml
- id: BE-001
  titulo: ...
  area: backend|frontend|infra
  depende_de: []
  arquivos: [backend/app/auth.py]   # diretórios/arquivos que o ticket toca
  criterios_aceite: [...]
  testes: [...]
```
Tickets pequenos (meio dia de trabalho humano no máximo). Inclua os riscos altos
do MVP como tickets ou critérios de aceite. Cada item de `security_requirements`
deve aparecer como critério de aceite (com teste) em pelo menos um ticket;
liste no ticket o campo `security_reqs: [SR-001, ...]`.

**Ticket de bootstrap obrigatório:** o primeiro ticket é sempre `INFRA-000`, sem
dependências, e todos os outros dependem dele. Ele cria a estrutura de pastas,
o runner de testes unitários (com um teste trivial passando), o linter, o
`.gitignore`, o `.env.example` e **todas as dependências previstas pela spec**.

**Manifestos de dependência** (`package.json`, lockfiles, `requirements.txt`,
`pyproject.toml`, `*.csproj`, `go.mod`...) só aparecem em `arquivos` do
`INFRA-000` ou de tickets de infra dedicados. Ticket comum não os lista; se o
implementador precisar de um pacote novo, ele pede ao orquestrador, que o
adiciona entre ondas.

## 6. assign-to-agents → scaffold-router (haiku)

O router lê `tickets.yaml` e `references/model-routing.md` e gera
`.project/agent-map.json`:
```json
{ "ondas": [
    { "onda": 1, "tickets": [
      {"id": "BE-001", "area": "backend", "complexity": "alta",
       "model": "opus", "motivo": "autenticação"} ] } ] }
```
Ondas respeitam `depende_de`. Dentro de uma onda, dois tickets **não podem**
tocar os mesmos arquivos (evita conflito na execução paralela).

Mostre ao usuário: total de tickets, quantos em opus/sonnet/haiku, número de
ondas e tempo estimado (soma dos orçamentos de `watchdog.md` pela onda mais
lenta). **Espere aprovação explícita** antes do estágio 7, o mais caro. Se o
usuário pedir, rebaixe tickets ou aplique `--economico` e reenvie ao router.

## 7. implement → scaffold-implementer (paralelo por onda)

Para cada onda, em ordem:
- Lance um `scaffold-implementer` por ticket, **em paralelo**, passando
  `model` = o valor do `agent-map.json` para aquele ticket.
- Cada implementador recebe no prompt: o ticket, os trechos relevantes da spec
  e do design, a regra de só mexer nos arquivos listados, e o **texto** das
  regras de código seguro de `references/security.md` (parte B).
- Testes unitários rodados durante a onda não podem depender de banco real,
  porta fixa ou serviço externo (vários implementadores rodam ao mesmo tempo na
  mesma pasta). Testes que precisam disso ficam para o estágio 8.
- Registre START de cada um em `.project/runs.log`. A cada subagente que
  termina, faça a verificação de `references/watchdog.md` nos que ainda rodam.
- Ao terminar a onda, rode os testes unitários da área. Aplique o escalonamento
  de `model-routing.md` se falharem.
- Commit por onda: `scaffold(7): onda N`.

## 8. tests → scaffold-tester

Escreva testes de integração cobrindo os fluxos de `user-flows.md`, os riscos
altos e os `security_requirements` (ex.: webhook sem assinatura é rejeitado,
pagamento não duplica cobrança). Rode tudo. Gere `.project/test-report.md` com:
comandos usados, resultado real, cobertura real (se a ferramenta medir).
Só números que a ferramenta mostrou.

## 9. security → scaffold-security + scaffold-implementer

Siga `references/security.md`, parte C, na ordem:

1. **9.1 audit** — rode as ferramentas e peça ao `scaffold-security` (opus) a
   revisão manual. Saída: `.project/security/findings.yaml`.
2. **9.2 triage** — `scaffold-security` classifica cada achado. Baixo e falso
   positivo justificado vão para `risks.yaml` (`tech_debt`) e não bloqueiam.
3. Se não sobrar crítico, alto ou médio: vá para o estágio 10.
4. Se houver **médio**: pergunte ao usuário, para cada um, "corrigir" ou
   "aceitar o risco". Aceite vira registro em `.project/security/accepted.md`
   com a justificativa dele.
5. **9.3 fix** — para cada SECURITY-00X a corrigir, lance um
   `scaffold-implementer` com `model: opus`. Primeiro ele escreve o teste que
   reproduz a falha (precisa falhar), depois corrige.
6. **9.4 verify** — `scaffold-security` (não o implementador) confere os três
   critérios da parte C. Se reprovar, volta ao 9.3 com o motivo. **Máximo de
   2 tentativas de correção por ticket**; depois disso, pare e pergunte ao
   usuário o que fazer.

Commit ao fim do 9.2 (`scaffold(9): security triage`) e a cada ticket
verificado (`scaffold(9): fix SECURITY-00X`).

## 10. code-review → scaffold-reviewer (pausa)

O reviewer é somente leitura. Gera `.project/code-review-report.md` com achados
classificados como crítico/importante/sugestão, cada um com arquivo e linha.
Rode também os linters do projeto, se existirem. A segurança já foi auditada no
estágio 9: o reviewer foca em corretude e manutenção, mas ainda registra
qualquer problema de segurança que notar.

Apresente o resumo ao usuário e **pergunte** se quer que os críticos sejam
corrigidos (em opus) antes de seguir.

## 11. final → testes + rescan + gate

1. Rode a suíte completa de testes (unitários + integração).
2. Rode o **rescan rápido** de `references/security.md`, parte D (só
   ferramentas, sem o agente de segurança, exceto se aparecer achado novo).
3. **Gate:** o pipeline só termina como "concluído" se:
   - todos os testes passam;
   - não há achado crítico ou alto aberto;
   - todo achado médio aberto está em `accepted.md`.
   Se algo falhar, mostre o motivo e pergunte ao usuário: corrigir agora, ou
   encerrar como "concluído com pendências" (registrado no relatório).
4. Gere `.project/pipeline-report.md`: estágios, modelos usados, escaladas,
   resultado dos testes, resumo de segurança (achados por severidade:
   corrigidos, aceitos, em dívida), pendências. Commit final.
