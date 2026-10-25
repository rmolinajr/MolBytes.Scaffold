# Mapa do código

`.project/mapa-codigo.md` diz **onde fica cada coisa** no código do projeto,
para os agentes não redescobrirem o sistema a cada rodada. É um índice, não
uma cópia: o mapa diz onde olhar, o código diz o que é. Quem decide ou altera
algo lê no código os arquivos que o mapa apontou.

Mapa desatualizado é pior que nenhum: o agente confia nele e decide em cima
do que já mudou. Por isso ele tem carimbo de commit, é atualizado pelo diff e
entra no gate.

## Formato

```markdown
# Mapa do código

Commit: <sha do último commit de código mapeado>
Atualizado: <data> — <origem: geração | estágio 11 da <fase>>

## Visão
- Stack: <linguagens, frameworks, banco, uma linha>
- Comandos: build `<cmd>` · testes `<cmd>` · lint `<cmd>` · rodar `<cmd>`
- Configuração: variáveis de ambiente lidas em <arquivo> (só os nomes)

## Estrutura
- `backend/app/` — API HTTP (FastAPI), um módulo por recurso
- `frontend/src/` — SPA (React), telas em `pages/`, chamadas à API em `api/`
- ...

## Pontos de entrada
- `backend/app/main.py` — cria o app e registra as rotas
- ...

## Módulos
- **Pedidos** — `backend/app/orders/` (rotas, serviço, modelo); usa Pagamentos
- ...

## Contratos
- Endpoints: `backend/app/*/routes.py` (prefixo `/api/v1`); OpenAPI em <arquivo>
- Banco: modelos em `backend/app/*/models.py`, migrações em `backend/migrations/`
- Eventos, filas, webhooks: <arquivo> | nenhum

## Arquivos de registro
- `frontend/src/i18n/pt-BR.json` — tradução de cada status e ação
- ...

## Convenções
- <padrões que o código já segue: nomes, camadas, padrão de testes>
```

Regras:

- Cada item tem caminho. Nada de código, assinatura ou trecho copiado.
- Máximo de ~15 mil caracteres. Sistema grande: agrupe por pasta, não por
  arquivo.
- Nenhum segredo nem valor de configuração: de `.env` e afins, só os nomes
  das variáveis.
- `Commit:` é o último commit que mexe em código, fora da pasta de
  documentos: `git log -1 --format=%h -- . ':(exclude).project'` (no modo
  externo, o `HEAD` do projeto).
- "Arquivos de registro" segue a definição do estágio 5 (`stages.md`): é onde
  o planner procura o dono no modo alteração.

## Gerar

- **Modo alteração:** antes do estágio 1, depois do ponto de partida
  (`alteracao.md`) e das extensões, se o mapa não existir.
- **Modo novo:** no fim do estágio 7, depois do commit da última onda.

Lance o `scaffold-architect` (medio) com: o caminho do mapa, o formato acima
colado no prompt, o `Commit:` a gravar e a regra "leia a estrutura de pastas,
os manifestos, os pontos de entrada e um ou dois arquivos por módulo; não leia
o código inteiro". Se uma extensão tiver trecho para o mapa (onde olhar em
cada stack, por exemplo), cole-o também; o formato do mapa não muda. Registre
no `runs.log` como `mapa do código`.

## Atualizar

O mapa é atualizado pelo diff, nunca refeito do zero (só se o `Commit:` não
existir mais no histórico, depois de um rebase, por exemplo):

1. Rode `git diff --name-status <Commit> HEAD -- . ':(exclude).project'` (no
   modo externo, no git do projeto). Vazio: o mapa está em dia, não lance
   nada.
2. Senão, lance o `scaffold-architect` (medio) com o caminho do mapa, a lista
   de arquivos do diff e o `Commit:` novo. Ele lê só esses arquivos e reescreve
   só as seções que eles afetam, mais as linhas `Commit:` e `Atualizado:`.

Quando:

- **Estágio 11**, antes do gate (o código das correções dos estágios 8 a 10
  também entra).
- **Começo de rodada nova** (modo alteração), se o diff não for vazio: o código
  mudou fora do pipeline desde a rodada anterior.

Os implementadores não editam o mapa: na mesma onda, todos editariam o mesmo
arquivo, e as ondas existem para que dois tickets nunca toquem o mesmo
arquivo.

## Quem lê

- **Estágio 1 (alteração):** você lê "Visão" e "Estrutura" (busca, não o
  arquivo inteiro) para não perguntar ao usuário o que o código já responde.
- **Estágio 2:** o architect parte do mapa e lê no código só as áreas que a
  alteração toca.
- **Estágio 5:** o planner preenche `arquivos` e acha os arquivos de registro
  pelo mapa, e copia em cada ticket o trecho do mapa que o ticket usa (os
  tickets continuam autossuficientes; o implementador não lê o mapa).
- **Estágios 8 e 11:** o tester usa "Comandos".

Antes de confiar no mapa, quem lê confere o diff do passo 1 de "Atualizar":
área com arquivo no diff se confirma no código.

## Gate e arquivamento

- **Gate do estágio 11:** o pipeline só fecha como "concluído" se o diff de
  `Commit:` até o `HEAD` do código estiver vazio.
- **Rodada nova:** o mapa fica na raiz da pasta de documentos, como a
  `spec.md`; a versão de cada fase fica no git.
