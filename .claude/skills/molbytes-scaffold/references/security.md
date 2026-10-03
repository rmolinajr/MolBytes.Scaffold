# Segurança no molbytes.scaffold

Segurança entra antes do código (partes A e B) e depois dele (partes C e D).
Isto reduz bastante o risco, mas não substitui um pentest profissional antes de
processar pagamentos reais.

---

## A. Modelo de ameaças (estágios 2 e 3)

### Na spec: seção "Segurança e dados pessoais"

1. **Dados pessoais:** tabela com dado, onde fica (servidor, SQLite local,
   logs, backups), quem acessa, por quanto tempo é guardado, base legal
   (LGPD/RGPD).
2. **Superfícies de ataque:** login, APIs públicas, webhooks (Stripe, PIX),
   sincronização offline, painel admin, uploads.
3. **Ameaças por superfície (STRIDE resumido):** quem falsifica identidade,
   adultera dados, nega ter feito algo, vaza informação, derruba o serviço,
   ganha permissão que não tem. Só as que se aplicam de verdade.
4. **Pagamentos:** cartão nunca passa pelo nosso servidor (Stripe Checkout ou
   Elements). Webhooks validados por assinatura. Operações de cobrança
   idempotentes.

### Em risks.yaml: `security_requirements`

```yaml
security_requirements:
  - id: SR-001
    requisito: "Webhook do Stripe só é processado com assinatura válida"
    ameaca: "Falsificação de confirmação de pagamento"
    teste: "POST no webhook sem assinatura retorna 400 e não altera o pedido"
```

---

## B. Regras de código seguro (estágio 7, para todo implementador)

- Nenhum segredo no código: tudo por variável de ambiente; `.env` no
  `.gitignore`; só `.env.example` com valores falsos.
- Queries sempre parametrizadas ou via ORM. Nunca concatenar SQL.
- Validar toda entrada externa no servidor (tipo, tamanho, formato).
- Autorização checada no servidor em todo endpoint, não só no frontend.
- Senhas com bcrypt ou argon2. Tokens com expiração.
- Não logar senha, token, dados de cartão ou documento pessoal.
- Dados de cartão nunca tocam o backend.
- Webhooks: validar assinatura antes de qualquer processamento.
- Dados locais sensíveis (SQLite do dispositivo) criptografados.
- Dependências com versão fixa; não adicionar pacote sem necessidade.

---

## C. Auditoria (estágio 9)

### 9.1 Ferramentas (via Docker, sem instalar nada no Windows)

Rode da raiz do projeto, no PowerShell. Saídas em `.project/security/raw/`.
Essa pasta **nunca vai para o git** (precisa estar no `.gitignore`): o relatório
do gitleaks contém os próprios segredos encontrados. O que vai para o git é o
`findings.yaml`, sem valores de segredo.
Se algum comando mudar de sintaxe numa versão nova da ferramenta, rode com
`--help`, ajuste, e anote o comando usado no relatório.

```powershell
mkdir -Force .project/security/raw

# Segredos no código e no histórico do git
docker run --rm -v "${PWD}:/repo" zricethezav/gitleaks:latest detect --source /repo --report-format json --report-path /repo/.project/security/raw/gitleaks.json

# Padrões inseguros no código (OWASP, injeção, etc.)
docker run --rm -v "${PWD}:/src" semgrep/semgrep semgrep scan --config auto --json -o /src/.project/security/raw/semgrep.json /src

# Dependências vulneráveis, segredos e configuração (Dockerfile, compose)
docker run --rm -v "${PWD}:/src" aquasec/trivy fs --scanners vuln,secret,misconfig --format json -o /src/.project/security/raw/trivy.json /src
```

Complementares, se o projeto tiver a stack correspondente:

```powershell
cd frontend; npm audit --json > ../.project/security/raw/npm-audit.json; cd ..
pip install pip-audit bandit
pip-audit -r backend/requirements.txt -f json -o .project/security/raw/pip-audit.json
bandit -r backend -f json -o .project/security/raw/bandit.json
```

Se o Docker não estiver rodando, avise o usuário em vez de pular as ferramentas.

### 9.1b Revisão manual (scaffold-security, opus)

Depois das ferramentas, revisar o código contra:
- OWASP Top 10 (controle de acesso, injeção, autenticação, configuração...);
- os `security_requirements` (cada um tem teste e está implementado?);
- fluxos de pagamento, webhook e sincronização offline, linha a linha.

### 9.2 Triagem → `.project/security/findings.yaml`

```yaml
- id: SECURITY-001
  origem: semgrep|gitleaks|trivy|npm-audit|pip-audit|bandit|manual
  severidade: critica|alta|media|baixa
  status: aberto|falso_positivo|aceito|divida|corrigido
  arquivo: backend/app/payments.py:88
  problema: "..."
  impacto: "o que um atacante consegue fazer"
  correcao: "..."
  teste_reproducao: "como provar que a falha existe"
```

Regras:
- **crítica:** exploração remota sem login, segredo real exposto, cobrança
  manipulável, vazamento em massa de dados pessoais.
- **alta:** exige login comum, ou expõe dados de outro usuário.
- **média:** exige condições específicas ou impacto limitado.
- **baixa:** boa prática, defesa em profundidade.
- Falso positivo só com justificativa concreta (ex.: "valor vem de constante,
  não de entrada do usuário"). Na dúvida, não é falso positivo.
- Achados duplicados entre ferramentas viram um só.
- Baixa e falso positivo → `risks.yaml` em `tech_debt`, status `divida` ou
  `falso_positivo`, não bloqueiam.

### 9.3 Correção (scaffold-implementer, sempre opus)

Ordem obrigatória:
1. Escrever o teste que reproduz a falha e rodar: **tem que falhar**.
2. Corrigir apenas o necessário.
3. Rodar o teste de reprodução e a suíte da área.

### 9.4 Verificação (scaffold-security, nunca o mesmo que corrigiu)

O ticket só é `corrigido` se os três passarem:
1. o teste de reprodução agora passa;
2. a ferramenta que achou o problema (se foi ferramenta) não acusa mais;
3. a suíte completa de testes continua passando (sem regressão).

Reprovou: volta ao 9.3 com o motivo. Máximo 2 tentativas; depois, perguntar ao
usuário: tentar de outra forma, aceitar o risco, ou parar.

---

## D. Rescan rápido (estágio 11)

Só gitleaks, trivy e semgrep da parte C, comparando com `findings.yaml`.
- Nada novo: segue para o gate.
- Achado novo: `scaffold-security` faz a triagem só dele; crítico ou alto
  bloqueia o gate.
