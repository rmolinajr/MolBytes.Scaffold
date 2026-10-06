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

- Grave em `state.md` o commit atual do projeto como `base_commit`.
- Rode a suíte de testes existente, se houver, e registre em `state.md` quais
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

Para documentação em pasta fora do projeto, avise uma vez que o Claude Code
precisa de permissão para ela (`additionalDirectories` ou `/add-dir`, como em
`documentos.md`).

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
  (`git diff <base_commit>`) vira `tech_debt` com `preexistente: true` e não
  bloqueia; aparece no relatório.
- Estágio 2: se `spec.md` já existir de um uso anterior da skill, atualize-a
  com a alteração em vez de reescrever.
