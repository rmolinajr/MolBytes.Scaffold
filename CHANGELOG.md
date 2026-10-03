# Changelog

Todas as mudanças relevantes do molbytes.scaffold.

## v0.5

- Ticket `INFRA-000` obrigatório: estrutura, runner de testes, linter e todas as
  dependências antes da onda 1.
- Manifestos de dependência (`package.json`, lockfiles...) só em tickets de
  infra: acaba o conflito entre implementadores paralelos.
- Testes unitários sem banco, porta fixa ou serviço externo durante o estágio 7.
- Pausa para aprovação depois do estágio 6 (tickets por modelo, ondas, tempo
  estimado) antes do estágio 7, o mais caro.
- `.project/security/raw/` fora do git (o relatório do gitleaks contém os
  segredos achados); `findings.yaml` nunca guarda o valor do segredo.
- O orquestrador cola as regras no prompt dos subagentes: funciona com a skill
  instalada no projeto ou em `~/.claude/`.
- Reexecução de ticket também apaga arquivos novos (`git clean`).
- Texto genérico ("o usuário"), sem nomes nem caminhos pessoais.
- Licença MIT.
- `/agents` saiu do Claude Code: verificação agora por `/plugin` e parada por `/tasks`.
- Distribuição como plugin do Claude Code (`/plugin install molbytes@molbytes`).

## v0.4 — segurança

- Modelo de ameaças e dados pessoais (LGPD/RGPD) já na spec; `security_requirements`
  testáveis viram critérios de aceite dos tickets.
- Regras de código seguro para todo implementador.
- Novo estágio 9: audit → triage → fix → verify, com o novo subagente
  `scaffold-security` (opus).
- Achado médio: o usuário decide corrigir ou aceitar o risco (fica registrado).
- Correção sempre começa por um teste que reproduz a falha; verificação feita
  por outro agente; no máximo 2 tentativas por achado.
- Estágio 11: testes finais + rescan rápido + gate (não termina com crítico ou
  alto aberto).

## v0.3

- `maxTurns` em todos os subagentes: o Claude Code encerra quem passar do limite.
- Orçamento de tempo por ticket/estágio, registrado em `.project/runs.log`.
- Aviso quando um subagente passa de 2x o tempo esperado.
- Comando `status` para ver o que está rodando e há quanto tempo.
- Para ver ou parar um subagente: `/agents` (aba Running) ou `/tasks`.
- Reexecução automática um nível de modelo acima quando um agente trava.

## v0.2

- `.project/state.md`: checkpoint atualizado a cada estágio.
- Pontos de compactação sugeridos nos estágios 2, 5 e 7.
- Retomada por `continuar` após /compact ou em sessão nova.
- Recomendação de `/autocompact 500k`.
