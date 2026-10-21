# Modelo de .project/state.md

Reescreva o arquivo inteiro ao fim de cada estágio. Não acumule histórico aqui
(o histórico está no git e em model-log.md).

```markdown
# Estado do scaffold

Projeto: <uma linha>
Fase: <nome curto da rodada, ex.: fase2>
Fases anteriores: <fase1, ...> | nenhuma
Plataforma: claude-code | codex | gemini-cli | cursor
Modelos: <só se diferente da tabela de plataformas.md: leve=..., medio=..., forte=...>
Documentos: <caminho da pasta de documentos (.project/ ou externa)>
Modo: novo | alteração (base_commit <sha>)
Flags: <ex.: --sem-design --ate tickets> | nenhuma
Extensão: <nome da skill de extensão carregada> | nenhuma
Testes que já falhavam: <lista ou "nenhum">   (modo alteração)
Documentação do sistema: docs-sistema.yaml | nenhuma   (modo alteração)
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
- Concluídos: BE-001 (forte), BE-002 (medio), ...
- Falharam/escalados: FE-003 medio→forte (testes falharam 2x)

## Plano de teste (a partir do estágio 8)
- Itens: passou X, falhou X, bloqueado X, manual X, aceito X
- Em correção: TP-007 (tentativa 1 de 2)

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
