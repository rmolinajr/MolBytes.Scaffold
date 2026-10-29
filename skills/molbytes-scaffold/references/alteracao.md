# Alteração de sistema existente

Quando o projeto já tem código, o pipeline altera o sistema e, se o sistema
tiver documentação, mantém essa documentação atualizada junto com o código.

A **documentação do sistema** (do cliente: README, `docs/`, manuais) é
diferente da **pasta de documentos** da skill (`references/documentos.md`),
que continua igual. A documentação do sistema nunca vai para a pasta de
documentos, e vice-versa.

## Escolher o modo

Depois de resolver a pasta de documentos e antes das extensões:

- Raiz do projeto sem código e sem `state.md`: **modo novo**, sem perguntar.
- Existe código: pergunte
  > Isto é um projeto novo ou uma alteração no sistema que já existe?

Registre em `state.md`: `Modo: novo` ou `Modo: alteração`.

## Antes do estágio 1 (modo alteração)

### 1. Ponto de partida

O `base_commit` separa o que já existia do que a rodada muda: testes que já
falhavam, achados de segurança preexistentes (estágio 9) e o `Commit:` do mapa
do código dependem dele. Ele precisa ser um commit que contém o código como o
usuário o entregou, sem nada a mais e sem nada a menos.

1. **Sem git, ou git sem nenhum commit** (`git rev-parse HEAD` falha): rode
   `git init` se preciso, garanta o `.gitignore` das regras gerais do
   `SKILL.md` e mostre ao usuário o que vai entrar no commit (`git status
   --short`, agrupado por pasta se for longo). Peça que confira se há algo que
   não deve ir para o git (credenciais, certificados, dumps de banco) e, com
   o sim, faça o commit `scaffold(0): ponto de partida` com o código e o
   `.gitignore`, sem a pasta de documentos
   (`git add -A -- . ':(exclude).project'`). O commit é só local: não
   configure remoto nem faça push.
2. **Alterações não commitadas** (`git status --porcelain` não vazio, sem
   contar a pasta de documentos nem o `.gitignore` que você acabou de
   ajustar): não comece. Diga quantos arquivos e pergunte
   > Há N arquivos alterados e não commitados. Antes de começar:
   > 1. commito como estão (`scaffold(0): ponto de partida`)
   > 2. você commita ou guarda (`git stash`) e me avisa

   Com 1, faça o commit (também sem a pasta de documentos); com 2, espere e
   confira de novo. Sem isso, essas mudanças entrariam no diff como se fossem
   da rodada.
3. Grave em `state.md` o commit atual do projeto (`HEAD`) como `base_commit`.
4. Rode a suíte de testes existente, se houver, e registre em `state.md` quais
   testes **já falham antes da alteração**. Essas falhas não bloqueiam o gate,
   desde que não piorem.

### 2. Documentação do sistema

1. **Procure no projeto:** pastas `docs/`, `doc/`, `documentation/`, `wiki/`,
   `adr/`, e arquivos `README*`, `CHANGELOG*`, `openapi.*`/`swagger.*`, manuais.
   Ignore dependências e build (`node_modules/`, `vendor/`, `bin/`, `obj/`,
   `dist/`) e a pasta de documentos da skill.
2. **Achou:** mostre a lista ao usuário e pergunte se há mais documentação
   fora do projeto.
3. **Não achou:** pergunte
   > Não encontrei documentação no projeto. O sistema tem documentação em outro
   > lugar? Se sim, onde (pasta ou link)?
4. **Sem documentação:** registre `Documentação do sistema: nenhuma` em
   `state.md` e siga só alterando o sistema. As regras de documentação abaixo
   não se aplicam.
5. **Com documentação:** grave a lista em `docs-sistema.yaml` na pasta de
   documentos:

```yaml
documentos:
  - caminho: README.md
    cobre: instalação, comandos, variáveis de ambiente
    onde: projeto        # projeto | pasta | site
  - caminho: D:/Docs/Cliente/manual-operador.md
    cobre: manual do operador de caixa
    onde: pasta          # pasta no disco fora do projeto: atualizada como as outras
  - caminho: https://empresa.atlassian.net/wiki/...
    cobre: guia de integração
    onde: site           # não dá para editar: vira aviso no relatório
  - caminho: docs/api/openapi.yaml
    cobre: contratos REST
    onde: projeto
    gerado_por: <comando que gera>   # se for gerado: atualizar pela fonte
```

Para documentação em pasta fora do projeto, avise uma vez que a plataforma
precisa de permissão para ela (como em `documentos.md`).

### 3. Mapa do código

Depois de carregar as extensões (`extensoes.md`), para o que elas acrescentam
ao mapa entrar no prompt. Sem `mapa-codigo.md` na pasta de documentos, gere-o; com ele, atualize-o se o
código mudou desde o `Commit:` (`references/mapa-codigo.md`). O mapa não é
documentação do sistema: fica na pasta de documentos e não entra em
`docs-sistema.yaml`.

### 4. Histórico

Com `historico.md` na pasta de documentos: se a atualização do mapa achou
diff, escreva no topo a entrada `fora do pipeline` (commits e áreas). Depois
leia as 3 entradas do topo e diga ao usuário, em uma linha, a última rodada e
o que ficou pendente (`references/historico.md`).

## Regras de documentação nos estágios

Só quando há `docs-sistema.yaml`:

- **Estágio 2:** a spec ganha a seção "Documentação afetada": que documentos
  a alteração deixa desatualizados e em que trecho. Se nenhum, diga o motivo.
- **Estágio 5:** cada ticket que deixa um documento desatualizado lista-o no
  campo `docs` e também em `arquivos`. Documento gerado entra pela fonte e pelo
  comando de geração. Documento `site` não entra em ticket.
- **Estágio 7:** o implementador atualiza os documentos do ticket no mesmo
  trabalho do código, só no trecho afetado e no formato que já existe.
- **Estágio 10:** o reviewer confere se cada documento da "Documentação
  afetada" bate com o código. Documento desatualizado é achado importante.
- **Estágio 11 (gate):** não fecha como "concluído" se algum documento
  `projeto` ou `pasta` da "Documentação afetada" não foi atualizado. Documento
  `site` vai para o relatório como "atualizar manualmente: <documento>,
  <trecho>".

## Outras regras do modo alteração

- Testes (estágios 8 e 11): falha que já existia no ponto de partida não é da
  alteração; falha nova é e bloqueia.
- Segurança (estágio 9): achado em código que a alteração não tocou
  (`git diff <base_commit>`) fica com status `divida` e vai para `tech_debt`
  com `preexistente: true`; não bloqueia e aparece no relatório.
- Estágio 10: depois do code review, o impacto fora do diff (`stages.md`,
  estágio 10) grava `impacto.md`; o gate do estágio 11 confere que todo `bug`
  foi corrigido e todo `não provado` de impacto alto foi corrigido ou aceito.
- Estágio 2: se `spec.md` já existir de um uso anterior da skill, atualize-a
  com a alteração em vez de reescrever.
- Estágio 3 curto: só os riscos e requisitos de segurança que a alteração
  introduz ou toca. Se não houver nenhum, `risks.yaml` sai com as listas
  vazias e um `motivo:` dizendo por quê (o planner e o tester leem o arquivo).
- Estágio 4: se a alteração não muda telas nem fluxos de usuário, proponha
  pular o design ("A mudança não mexe em telas; pulo o design?"). Com o sim,
  registre `--sem-design` em `Flags:` do `state.md`.
