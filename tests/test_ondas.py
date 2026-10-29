"""Testes de skills/molbytes-scaffold/scripts/ondas.py.

    python -m unittest discover tests
"""
import importlib.util
import json
import pathlib
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("ondas", RAIZ / "skills" / "molbytes-scaffold" / "scripts" / "ondas.py")
ondas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ondas)

INDICE = """\
convencoes:
  - testes com pytest
tickets:
- id: INFRA-000
  titulo: Estrutura
  area: infra
  depende_de: []
  arquivos: [pyproject.toml, src/]
- id: BE-001
  titulo: "Login: sessão"
  area: backend
  depende_de: [INFRA-000]
  arquivos: [src/auth/login.py, tests/test_login.py]
- id: BE-002
  area: backend
  depende_de: [INFRA-000]
  arquivos:
    - src/auth/            # diretório: conflita com o login
- id: FE-001
  area: frontend
  depende_de: [BE-001]
  arquivos: ["web/login.html"]
- id: FE-002
  area: frontend
  depende_de:
    - INFRA-000
  arquivos: [web/home.html]
"""


def classe(tid, model="medio", motivo=""):
    return {"id": tid, "area": "", "complexity": "media", "model": model, "motivo": motivo}


TODOS = [classe("INFRA-000", "leve"), classe("BE-001", "forte", "auth"), classe("BE-002"),
         classe("FE-001"), classe("FE-002", "leve")]


def ondas_de(mapa):
    return {t["id"]: o["onda"] for o in mapa["ondas"] for t in o["tickets"]}


class LerIndice(unittest.TestCase):
    def test_listas_em_linha_e_em_bloco(self):
        tickets = {t["id"]: t for t in ondas.ler_indice(INDICE)}
        self.assertEqual(list(tickets), ["INFRA-000", "BE-001", "BE-002", "FE-001", "FE-002"])
        self.assertEqual(tickets["BE-002"]["arquivos"], ["src/auth/"])
        self.assertEqual(tickets["FE-002"]["depende_de"], ["INFRA-000"])
        self.assertEqual(tickets["FE-001"]["arquivos"], ["web/login.html"])
        self.assertEqual(tickets["BE-001"]["area"], "backend")

    def test_ticket_com_recuo_e_lista_em_varias_linhas(self):
        texto = "tickets:\n  - id: A-1\n    depende_de: [\n      X, Y]\n    arquivos: []\nresumo: fim\n"
        (ticket,) = ondas.ler_indice(texto)
        self.assertEqual(ticket["depende_de"], ["X", "Y"])


class Montar(unittest.TestCase):
    def montar(self, indice=INDICE, classificacao=TODOS):
        return ondas.montar(ondas.ler_indice(indice), classificacao)

    def test_infra_sozinho_dependencias_e_conflito_de_diretorio(self):
        mapa, erros, _ = self.montar()
        self.assertEqual(erros, [])
        self.assertEqual(ondas_de(mapa), {"INFRA-000": 1, "BE-001": 2, "FE-002": 2, "BE-002": 3, "FE-001": 3})
        self.assertEqual(mapa["ondas"][0]["tickets"][0]["area"], "infra")   # vem do índice

    def test_dependencia_nunca_na_mesma_onda_nem_depois(self):
        mapa, _, _ = self.montar()
        onda = ondas_de(mapa)
        for t in ondas.ler_indice(INDICE):
            for dep in t["depende_de"]:
                self.assertLess(onda[dep], onda[t["id"]])

    def test_mesmo_resultado_em_toda_execucao(self):
        self.assertEqual(self.montar()[0], self.montar()[0])

    def test_ticket_inventado_duplicado_e_faltando(self):
        classes = TODOS[:-1] + [classe("BE-001"), classe("BE-999")]
        mapa, erros, _ = self.montar(classificacao=classes)
        self.assertIsNone(mapa)
        texto = "\n".join(erros)
        self.assertIn("BE-001 aparece mais de uma vez", texto)
        self.assertIn("BE-999 não está no tickets.yaml", texto)
        self.assertIn("FE-002 não foi classificado", texto)

    def test_nivel_invalido_e_forte_sem_motivo(self):
        classes = [classe("INFRA-000", "gigante"), classe("BE-001", "forte")] + TODOS[2:]
        _, erros, _ = self.montar(classificacao=classes)
        self.assertTrue(any("nível inválido" in e for e in erros))
        self.assertTrue(any("BE-001 em forte sem motivo" in e for e in erros))

    def test_nomes_do_claude_valem_como_nivel(self):
        classes = [dict(c, model={"leve": "haiku", "medio": "sonnet", "forte": "opus"}[c["model"]]) for c in TODOS]
        mapa, erros, _ = self.montar(classificacao=classes)
        self.assertEqual(erros, [])
        self.assertEqual({t["model"] for o in mapa["ondas"] for t in o["tickets"]}, {"leve", "medio", "forte"})

    def test_dependencia_inexistente_e_ciclo(self):
        _, erros, _ = self.montar(INDICE.replace("depende_de: [BE-001]", "depende_de: [BE-404]"))
        self.assertTrue(any("depende de BE-404, que não existe" in e for e in erros))
        ciclo = INDICE.replace("- id: BE-001\n  titulo: \"Login: sessão\"\n  area: backend\n  depende_de: [INFRA-000]",
                               "- id: BE-001\n  area: backend\n  depende_de: [FE-001]")
        _, erros, _ = self.montar(ciclo)
        self.assertTrue(any("ciclo" in e and "BE-001" in e and "FE-001" in e for e in erros))

    def test_id_duplicado_no_indice(self):
        _, erros, _ = self.montar(INDICE + "- id: FE-002\n  area: frontend\n  depende_de: []\n  arquivos: [x]\n")
        self.assertTrue(any("FE-002 aparece mais de uma vez" in e for e in erros))

    def test_sem_infra_comeca_na_onda_1(self):
        indice = "tickets:\n- id: A\n  depende_de: []\n  arquivos: [a.py]\n- id: B\n  depende_de: []\n  arquivos: [a.py]\n"
        mapa, erros, _ = ondas.montar(ondas.ler_indice(indice), [classe("A"), classe("B")])
        self.assertEqual(erros, [])
        self.assertEqual(ondas_de(mapa), {"A": 1, "B": 2})


RISCOS = """\
risks:
- id: RISK-001
  titulo: Pagamento duplicado
security_requirements:
  - id: SR-001
    requisito: "Webhook só com assinatura válida"
  - id: "SR-002"   # entre aspas
    requisito: Senha com bcrypt
tech_debt:
  - id: TD-001
"""


class Requisitos(unittest.TestCase):
    def test_le_so_a_lista_de_requisitos(self):
        self.assertEqual(ondas.ler_requisitos(RISCOS), ["SR-001", "SR-002"])
        self.assertEqual(ondas.ler_requisitos("risks: []\n"), [])

    def test_requisito_sem_ticket_e_ticket_com_requisito_inexistente(self):
        indice = INDICE.replace("arquivos: [src/auth/login.py, tests/test_login.py]",
                                "arquivos: [src/auth/login.py, tests/test_login.py]\n  security_reqs: [SR-001, SR-009]")
        mapa, erros, _ = ondas.montar(ondas.ler_indice(indice), TODOS, ["SR-001", "SR-002"])
        self.assertIsNone(mapa)
        texto = "\n".join(erros)
        self.assertIn("SR-002 (risks.yaml) não está em `security_reqs` de nenhum ticket", texto)
        self.assertIn("BE-001 lista SR-009 em `security_reqs`, que não existe no risks.yaml", texto)
        self.assertTrue(all(e.startswith("tickets.yaml:") for e in erros))   # erro do estágio 5

    def test_cobertos_em_bloco_passam_e_sem_risks_nao_confere(self):
        indice = INDICE.replace("  arquivos: [web/home.html]\n",
                                "  arquivos: [web/home.html]\n  security_reqs:\n    - SR-001\n    - SR-002\n")
        self.assertEqual(ondas.montar(ondas.ler_indice(indice), TODOS, ["SR-001", "SR-002"])[1], [])
        self.assertEqual(ondas.montar(ondas.ler_indice(INDICE), TODOS, None)[1], [])

    def test_linha_de_comando_le_o_risks_yaml(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = pathlib.Path(pasta)
            (p / "tickets.yaml").write_text(INDICE, encoding="utf-8")
            (p / "classificacao.json").write_text(json.dumps(TODOS), encoding="utf-8")
            (p / "risks.yaml").write_text(RISCOS, encoding="utf-8")
            self.assertEqual(ondas.main([pasta]), 1)
            self.assertFalse((p / "agent-map.json").exists())


class Conflito(unittest.TestCase):
    def test_caminhos(self):
        self.assertTrue(ondas.conflitam(["src/auth/"], ["src/auth/login.py"]))
        self.assertTrue(ondas.conflitam(["./src\\auth\\x.py"], ["src/auth/x.py"]))
        self.assertTrue(ondas.conflitam(["src/**/*.py"], ["src/a/b.py"]))
        self.assertFalse(ondas.conflitam(["src/auth.py"], ["src/auth2.py"]))
        self.assertFalse(ondas.conflitam(["src/auth"], ["src/authz/x.py"]))
        self.assertFalse(ondas.conflitam([], ["src/a.py"]))


class Linha(unittest.TestCase):
    def test_grava_e_resume_ou_nao_grava_com_erro(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = pathlib.Path(pasta)
            (p / "tickets.yaml").write_text(INDICE, encoding="utf-8")
            (p / "classificacao.json").write_text(json.dumps({"tickets": TODOS}), encoding="utf-8")
            self.assertEqual(ondas.main([pasta]), 0)
            mapa = json.loads((p / "agent-map.json").read_text(encoding="utf-8"))
            self.assertEqual(len(mapa["ondas"]), 3)
            self.assertEqual(ondas.resumo(mapa)[1], "Níveis: forte 1 (20%) · medio 2 · leve 2")

            (p / "agent-map.json").unlink()
            (p / "classificacao.json").write_text(json.dumps(TODOS[:-1]), encoding="utf-8")
            self.assertEqual(ondas.main([pasta]), 1)
            self.assertFalse((p / "agent-map.json").exists())

    def test_forte_acima_do_limite_lista_os_tickets(self):
        mapa = {"ondas": [{"onda": 1, "tickets": [classe("A", "forte", "auth"), classe("B")]}]}
        linhas = ondas.resumo(mapa)
        self.assertIn("- A: auth", linhas)


if __name__ == "__main__":
    unittest.main()
