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
   `.gitignore` com `security/raw/` (relatórios brutos contêm segredos).
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
   - para o Claude Code não pedir permissão a cada arquivo, adicione a
     pasta-mãe em `permissions.additionalDirectories` do
     `~/.claude/settings.json` (vale para todos os projetos), ou use `/add-dir`
     na sessão. Você não altera configurações do usuário.

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
