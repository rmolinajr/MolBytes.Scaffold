# Modelo de .project/state.md

Reescreva o arquivo inteiro ao fim de cada estágio. Não acumule histórico aqui
(o histórico está no git e em model-log.md).

```markdown
# Estado do scaffold

Projeto: <uma linha>
Atualizado: <data/hora> — fim do estágio <N> (<nome>)

## Estágios
- [x] 1 grill-me — .project/qa.json
- [x] 2 to-spec — aprovada pelo usuário em <data>
- [ ] 3 risks-tech-debt
...
- [ ] 9 security
- [ ] 10 code-review
- [ ] 11 final

## Decisões que valem para os próximos estágios
- Stack: ...
- Fora do MVP: ...
- Mudanças que o usuário pediu na spec: ...

## Estágio 7 (se em andamento)
- Onda atual: 2 de 4
- Concluídos: BE-001 (opus), BE-002 (sonnet), ...
- Falharam/escalados: FE-003 sonnet→opus (testes falharam 2x)

## Segurança (a partir do estágio 9)
- Achados: crítica X, alta X, média X, baixa X
- Corrigidos: SECURITY-001, ...
- Aceitos pelo usuário: SECURITY-004 (motivo curto)
- Em correção: SECURITY-002 (tentativa 1 de 2)

## Pendências
- ...

## Próximo passo
<ação exata que o orquestrador deve fazer em seguida>
```
