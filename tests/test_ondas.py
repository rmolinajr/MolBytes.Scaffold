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

    def test_comentario_depois_da_lista(self):
        # Numa rodada real, `depende_de: [A, B]  # motivo` virava a dependência «B]» e o mapa não saía.
        texto = ("tickets:\n- id: A-1\n  depende_de: [B-1, C-1]  # decidido em 13/11 (§0)\n"
                 "  arquivos: []  # nenhum\n- id: A-2\n  depende_de: [\n    B-1]  # fim\n")
        a1, a2 = ondas.ler_indice(texto)
        self.assertEqual(a1["depende_de"], ["B-1", "C-1"])
        self.assertEqual(a1["arquivos"], [])
        self.assertEqual(a2["depende_de"], ["B-1"])


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


class OndasFinas(unittest.TestCase):
    def cadeia(self, n):
        linhas = ["tickets:", "- id: INFRA-000", "  depende_de: []", "  arquivos: [infra/]"]
        anterior = "INFRA-000"
        for i in range(1, n + 1):
            tid = f"FE-{i:03d}"
            linhas += [f"- id: {tid}", f"  depende_de: [{anterior}]", f"  arquivos: [web/t{i}.html]"]
            anterior = tid
        indice = "\n".join(linhas) + "\n"
        ids = ["INFRA-000"] + [f"FE-{i:03d}" for i in range(1, n + 1)]
        mapa, erros, _ = ondas.montar(ondas.ler_indice(indice), [classe(t) for t in ids])
        self.assertEqual(erros, [])
        return mapa

    def test_cadeia_de_ordem_vira_aviso_no_resumo(self):
        texto = "\n".join(ondas.resumo(self.cadeia(6)))
        self.assertIn("Ondas de um ticket só: 7 de 7; 6 seguidas, da onda 2 à 7", texto)
        self.assertIn("FE-001 → FE-002", texto)

    def test_cadeia_curta_nao_avisa(self):
        self.assertNotIn("Ondas de um ticket só", "\n".join(ondas.resumo(self.cadeia(4))))

    def test_suite_completa_a_cada_5_ondas_e_na_ultima(self):
        mapa = self.cadeia(11)
        suites = {o["onda"]: o["suite"] for o in mapa["ondas"]}
        self.assertEqual([n for n, s in suites.items() if s == "completa"], [5, 10, 12])
        self.assertEqual(suites[1], "area")


class Replanejar(unittest.TestCase):
    """Estágio 7: ticket partido, tickets novos ou passar do fim do mapa replanejam pelo script."""

    INDICE_NOVO = INDICE + """\
- id: FE-003
  area: frontend
  depende_de: [FE-001]
  arquivos: [web/review.html]
- id: FE-004
  area: frontend
  depende_de: [FE-002]
  arquivos: [web/main.html]
- id: BE-010
  area: backend
  depende_de: [FE-003, FE-004]
  arquivos: [src/domain/]
"""

    def montar(self, feitos, fora=None, **kw):
        return ondas.montar(ondas.ler_indice(self.INDICE_NOVO), TODOS, None, feitos=feitos, fora=fora, **kw)

    def test_so_os_abertos_em_paralelo_e_numerados_a_partir_de_n(self):
        mapa, erros, avisos = self.montar(["INFRA-000", "BE-001", "BE-002", "FE-001", "FE-002"], inicio=118)
        self.assertEqual(erros, [])
        # Duas trilhas independentes lado a lado, não uma fila: FE-003 ∥ FE-004, depois BE-010.
        self.assertEqual(ondas_de(mapa), {"FE-003": 118, "FE-004": 118, "BE-010": 119})
        self.assertEqual(mapa["fonte"], "scripts/ondas.py --feitos")
        self.assertIn("classificação: FE-003 sem classificação; entra como medio", avisos)
        self.assertEqual(mapa["ondas"][-1]["suite"], "completa")
        self.assertIn("ondas-replano.json: 3 tickets em aberto em 2 ondas, da 118 à 119", ondas.resumo(mapa)[0])

    def test_ticket_do_mapa_esquecido_volta_ao_plano(self):
        # FE-002 não foi feito nem posto de fora: entra, e o FE-004 vem depois dele.
        mapa, _, _ = self.montar(["INFRA-000", "BE-001", "BE-002", "FE-001"])
        self.assertEqual(ondas_de(mapa), {"FE-002": 1, "FE-003": 1, "FE-004": 2, "BE-010": 3})

    def test_pai_partido_entra_pelas_pecas(self):
        indice = self.INDICE_NOVO + """\
- id: FE-003a
  depende_de: [FE-001]
  arquivos: [web/review.html]
- id: FE-003b
  depende_de: [FE-003a]
  arquivos: [web/review.html]
"""
        mapa, erros, avisos = ondas.montar(ondas.ler_indice(indice), TODOS, None,
                                           feitos=["INFRA-000", "BE-001", "BE-002", "FE-001", "FE-002"])
        self.assertEqual(erros, [])
        # FE-003 não roda; o BE-010, que dependia dele, espera o FE-003b.
        self.assertEqual(ondas_de(mapa), {"FE-003a": 1, "FE-004": 1, "FE-003b": 2, "BE-010": 3})
        self.assertIn("FE-003 partido em FE-003a, FE-003b: entra pelas peças", avisos)
        self.assertTrue(ondas._peca("BE-030C0", "BE-030C"))
        self.assertFalse(ondas._peca("FE-0200", "FE-020"))

        # O "pai" que depende das peças é o ticket que fecha a série: fica, depois delas.
        fecha = indice.replace("- id: FE-003\n  area: frontend\n  depende_de: [FE-001]",
                               "- id: FE-003\n  area: frontend\n  depende_de: [FE-001, FE-003b]")
        mapa, _, avisos = ondas.montar(ondas.ler_indice(fecha), TODOS, None,
                                       feitos=["INFRA-000", "BE-001", "BE-002", "FE-001", "FE-002"])
        self.assertEqual(ondas_de(mapa)["FE-003"], 3)
        self.assertFalse(any("FE-003 partido" in a for a in avisos))

    def test_fora_leva_junto_quem_depende_dele(self):
        mapa, erros, avisos = self.montar(["INFRA-000", "BE-001", "BE-002", "FE-001"], fora=["FE-002"])
        self.assertEqual(erros, [])
        self.assertEqual(ondas_de(mapa), {"FE-003": 1})
        self.assertIn("FE-004 fica fora também: depende de FE-002, que está fora", avisos)
        self.assertIn("BE-010 fica fora também: depende de FE-004, que está fora", avisos)

    def test_id_que_nao_existe_e_aviso(self):
        _, _, avisos = self.montar(["INFRA-000", "BE-001", "BE-002", "FE-001", "FE-002", "FE-999"])
        self.assertIn("--feitos: FE-999 não está no tickets.yaml", avisos)
        # Classificado e depois partido ou tirado do índice: aviso no replano (no estágio 6, erro).
        mapa, erros, avisos = ondas.montar(ondas.ler_indice(self.INDICE_NOVO), TODOS + [classe("FE-090A")], None,
                                           feitos=["INFRA-000"])
        self.assertEqual(erros, [])
        self.assertIn("classificação: FE-090A não está no tickets.yaml (ignorado)", avisos)

    def test_max_por_onda(self):
        mapa, _, _ = self.montar(["INFRA-000"], max_por_onda=2)
        self.assertTrue(all(len(o["tickets"]) <= 2 for o in mapa["ondas"]))
        self.assertEqual(sorted(ondas_de(mapa)), sorted(["BE-001", "BE-002", "FE-001", "FE-002", "FE-003", "FE-004", "BE-010"]))

    def test_linha_de_comando_grava_ondas_replano_e_nunca_o_agent_map(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = pathlib.Path(pasta)
            (p / "tickets.yaml").write_text(self.INDICE_NOVO, encoding="utf-8")
            (p / "classificacao.json").write_text(json.dumps(TODOS), encoding="utf-8")
            (p / "feitos.txt").write_text("INFRA-000, BE-001 BE-002\nFE-001  # onda 3\nFE-002\n", encoding="utf-8")
            self.assertEqual(ondas.main([pasta, "--feitos", str(p / "feitos.txt"), "--a-partir", "118"]), 0)
            self.assertFalse((p / "agent-map.json").exists())
            mapa = json.loads((p / "ondas-replano.json").read_text(encoding="utf-8"))
            self.assertEqual([o["onda"] for o in mapa["ondas"]], [118, 119])
            self.assertEqual(ondas.main([pasta, "--feitos", str(p / "feitos.txt"), "--saida", str(p / "agent-map.json")]), 2)
            self.assertEqual(ondas.main([pasta, "--a-partir", "118"]), 2)


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
