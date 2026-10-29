# Pasta de documentos

Os documentos do pipeline (qa, spec, riscos, design, tickets, relatórios,
estado) ficam na **pasta de documentos**. Ela pode estar dentro do projeto
(`.project/`, padrão) ou numa pasta separada escolhida pelo usuário, para não
misturar documentos com o código do cliente.

Em todo o pipeline, `.project/` significa "a pasta de documentos". Quando ela
for externa, troque `.project/` pelo caminho real.

## Resolver a pasta (antes do estágio 1 e sempre que retomar)

1. **`.project/` existe na raiz do projeto:** use-a (modo interno).
2. **Senão, procure o projeto no ponteiro** `~/.molbytes/projetos.json`
   (chave: caminho absoluto da raiz do projeto):
   - achou e a pasta existe, com `projeto.json` dentro: use-a (modo externo);
   - achou e a pasta **não** existe: diga exatamente
     > Não encontrei a pasta de documentos deste projeto em `<caminho>`.
     > Onde estão os documentos? Informe o caminho, ou diga `novo` para começar do zero.

     Confira se a pasta informada tem `projeto.json` deste projeto, atualize o
     ponteiro e siga. Não crie uma pasta nova sem o usuário dizer `novo`.
3. **Não achou nada:** é projeto novo (ou os documentos foram movidos). Pergunte:
   > Onde ficam os documentos do projeto (spec, design, relatórios)?
   > 1. Dentro do projeto, em `.project/`
   > 2. Em outra pasta (fora do projeto do cliente)
   > 3. Já existem documentos em outra pasta

   - **1:** crie `.project/` e siga o pipeline normal.
   - **2:** peça a pasta-mãe (ex.: `D:\Clientes`) e proponha
     `<pasta-mãe>/<nome-do-projeto>/` (nome = nome da pasta do projeto, em
     minúsculas, com hífens). Confirme o nome. Se a pasta já existir com
     `projeto.json` de outro projeto, não use: peça outro nome.
   - **3:** peça o caminho, confira o `projeto.json` e grave o ponteiro.

## Criar a pasta externa

1. Crie a pasta e grave `projeto.json`:
   ```json
   {
     "nome": "<nome-do-projeto>",
     "projeto": "<caminho absoluto da raiz do projeto>",
     "remoto": "<git remote do projeto, ou null>",
     "criado": "<data>"
   }
   ```
2. Se ela não for um repositório git, rode `git init` nela e crie um
   `.gitignore` com `**/security/raw/` (relatórios brutos contêm segredos; o
   `**` cobre também as fases arquivadas).
3. Grave ou atualize `~/.molbytes/projetos.json`:
   ```json
   {
     "projetos": {
       "<caminho absoluto da raiz do projeto>": {
         "documentos": "<caminho absoluto da pasta de documentos>",
         "atualizado": "<data>"
       }
     }
   }
   ```
4. Avise o usuário, em até três linhas:
   - a pasta precisa ficar em git para não haver perdas; sem um remoto
     (repositório privado), o git não protege contra perda do disco: sugira
     configurar um;
   - para a plataforma não pedir permissão a cada arquivo, autorize a
     pasta-mãe uma vez (como, em cada plataforma: "Pasta fora do projeto" em
     `references/plataformas.md`). Você não altera configurações do usuário.

Nada é criado no projeto do cliente no modo externo: nem ponteiro, nem link,
nem entrada no `.gitignore`.

## Durante o pipeline (modo externo)

- **Ao delegar**, comece o prompt com:
  `Pasta de documentos: <caminho absoluto>. Onde suas instruções dizem .project/, use esta pasta.`
- **Commits:** ao fim de cada estágio, faça o commit dos documentos no git da
  pasta de documentos e, se houve mudança de código, o commit do código no git
  do projeto. Mesma mensagem `scaffold(N): <estágio>` nos dois.
- **Retomada:** leia `state.md` da pasta de documentos e o `git log` dos dois
  repositórios.
- **Estado:** em `state.md`, registre na primeira linha
  `Documentos: <caminho>` para o usuário saber onde estão.

## Rodada nova numa pasta que já tem documentos

A rodada atual fica sempre na raiz da pasta de documentos (`.project/state.md`,
`.project/tickets.yaml`...). Nunca crie a rodada nova numa subpasta: a
retomada com `continuar` e as ferramentas que leem o estado procuram na raiz.

Vale também quando o projeto já tem fases em subpastas (`.project/fase2/`...)
criadas antes desta regra: elas ficam como estão, e a rodada nova vai para a
raiz. Numa execução real, a sessão seguiu essas subpastas e gravou a rodada
nova em `.project/fase2d/`, fora da raiz em que a retomada e as ferramentas
procuram.

**Quando é rodada nova:** `state.md` existe e o estágio 11 está marcado; a
raiz tem arquivos de uma rodada (`tickets.yaml`, `pipeline-report.md`...) sem
`state.md` (rodada de antes desta regra, já encerrada); ou o usuário diz que o
pedido é outra mudança e não a continuação da rodada que está lá. Rodada não
terminada: pergunte antes
> A rodada `<Fase:>` parou no estágio N. Continuo dela ou arquivo e começo
> outra?

e só arquive com a resposta `arquivar`.

**Arquivar a rodada anterior:**

1. **Nome da fase:** o `Fase:` do `state.md`. Sem ele (rodadas de antes desta
   regra), proponha `fase1`, ou o próximo número livre, e confirme. Minúsculas,
   com hífens, e nunca `design`, `security` ou `tickets` nem uma subpasta que
   já exista.
2. **`.gitignore`:** confira que cobre `security/raw/` também nas subpastas
   (`.project/**/security/raw/` no modo interno, `**/security/raw/` no
   externo). Se a entrada for a antiga, sem `**`, troque antes de mover.
3. **Mover** para `.project/<fase>/`, com `git mv` (ou `mv` no que não está no
   git), o que é só da rodada: `state.md`, `qa.json`, `risks.yaml`,
   `tickets.yaml`, `tickets/`, `classificacao.json`, `agent-map.json`,
   `regras-implementacao.md`, `plano-de-teste.yaml`, `testes-travados.txt`, `test-report.md`,
   `security/`, `code-review-report.md`, `impacto.md`, `pipeline-report.md`, `runs.log` e
   `model-log.md`. O que não existir, pule.
4. **Ficam na raiz e evoluem:** `spec.md`, `design/`, `docs-sistema.yaml`,
   `mapa-codigo.md` e `historico.md` descrevem o sistema inteiro. A rodada nova os atualiza (ver
   `alteracao.md`); a versão de cada fase fica no git.
5. **Commit:** `scaffold(0): arquiva <fase>` (no modo externo, no git da pasta
   de documentos).
6. **Estado novo:** `state.md` do modelo, com `Fase: <nome da rodada nova>`
   (proponha o próximo número e confirme) e `Fases anteriores: <fase>, ...`.
   Siga a escolha do modo (`alteracao.md`): com código, a rodada nova é
   alteração, com `base_commit` novo.
