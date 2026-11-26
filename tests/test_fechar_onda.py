"""Testes de skills/molbytes-scaffold/scripts/fechar-onda.py.

    python -m unittest discover tests
"""
import importlib.util
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("fechar_onda", RAIZ / "skills" / "molbytes-scaffold" / "scripts" / "fechar-onda.py")
fo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fo)

INDICE = """\
tickets:
- id: BE-001
  area: backend
  depende_de: []
  arquivos: [src/a.py]
  testes_alterados:
    - tests/test_b.py: o total passa a contar o cupom
- id: BE-002
  area: backend
  depende_de: [BE-001]
  arquivos: [src/c.py]
  testes_alterados:
    - arquivo: tests/test_c.py
      motivo: muda a mensagem
    - arquivo: tests/test_d.py
      motivo: idem
- id: BE-003
  area: backend
  depende_de: [BE-002]
  arquivos: [src/e.py]
  testes_alterados: [tests/test_e.py  # renomeado]
"""
MAPA = {"fonte": "scripts/ondas.py", "ondas": [
    {"onda": 1, "suite": "area", "tickets": [{"id": "BE-001", "model": "medio"}]},
    {"onda": 2, "suite": "completa", "tickets": [{"id": "BE-002", "model": "forte"}]},
]}


class TestFuncoes(unittest.TestCase):
    def test_testes_alterados_nas_tres_formas(self):
        indice = fo.ondas.ler_indice(INDICE)
        self.assertEqual(fo.aprovados(indice, ["BE-001"]), {"tests/test_b.py"})
        self.assertEqual(fo.aprovados(indice, ["BE-002"]), {"tests/test_c.py", "tests/test_d.py"})
        self.assertEqual(fo.aprovados(indice, ["BE-003"]), {"tests/test_e.py"})
        self.assertEqual(fo.aprovados(indice, ["FIX-1"]), set())

    def test_campo_dentro_de_item_nao_corta_a_lista(self):
        indice = fo.ondas.ler_indice(INDICE)
        be2 = next(t for t in indice if t["id"] == "BE-002")
        self.assertEqual(be2["depende_de"], ["BE-001"])
        self.assertEqual(len(be2["testes_alterados"]), 2)

    def test_caminho_mantem_ponto_inicial_e_tira_barra_invertida(self):
        self.assertEqual(fo.caminho_teste(".github/tests/x.yml (motivo)"), ".github/tests/x.yml")
        self.assertEqual(fo.caminho_teste("./tests\\unit\\a.cs — renomeado"), "tests/unit/a.cs")

    def test_travados_aceita_pasta_e_respeita_liberados(self):
        mudados = ["tests/a.py", "tests/b.py", "tests/unit/c.py", "src/x.py"]
        self.assertEqual(fo.travados_mudados(mudados, ["tests/a.py", "tests/b.py", "tests/unit/"], {"tests/b.py"}),
                         ["tests/a.py", "tests/unit/c.py"])

    def test_sha_travado_ignora_ainda_nao(self):
        self.assertEqual(fo.sha_travado("x\nTestes travados: ab12cd3\n"), "ab12cd3")
        self.assertIsNone(fo.sha_travado("Testes travados: ainda não\n"))

    def test_acrescentar_nao_repete(self):
        texto, novos = fo.acrescentar("BE-001\n", ["BE-001", "BE-002", "BE-002"])
        self.assertEqual((texto, novos), ("BE-001\nBE-002\n", ["BE-002"]))
        self.assertEqual(fo.acrescentar(texto, ["BE-002"]), (texto, []))

    def test_worktrees_separa_subagente_das_outras(self):
        porcelana = ("worktree /p/proj\nHEAD 1\nbranch refs/heads/main\n\n"
                     "worktree /p/proj/.claude/worktrees/agent-a1\nHEAD 2\nbranch refs/heads/worktree-agent-a1\n\n"
                     "worktree /p/proj/.claude/worktrees/feliz-turing\nHEAD 3\nbranch refs/heads/claude/feliz-turing\n")
        sub, outras = fo.worktrees(porcelana, "/p/proj")
        self.assertEqual(len(sub), 1)
        self.assertIn("agent-a1", sub[0])
        self.assertEqual(len(outras), 1)


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout.decode("utf-8").strip()


class TestComando(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name) / "proj"
        (self.repo / "tests").mkdir(parents=True)
        self.docs = self.repo / ".project"
        self.docs.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "t@t")
        _git(self.repo, "config", "user.name", "t")
        for nome in ("test_a.py", "test_b.py"):
            (self.repo / "tests" / nome).write_text("x = 1\n", encoding="utf-8")
        (self.docs / "tickets.yaml").write_text(INDICE, encoding="utf-8")
        (self.docs / "agent-map.json").write_text(json.dumps(MAPA), encoding="utf-8")
        (self.docs / "testes-travados.txt").write_text("tests/test_a.py\ntests/test_b.py\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "base")
        self.sha_travado = _git(self.repo, "rev-parse", "HEAD")
        self.gravar_estado()

    def tearDown(self):
        self.tmp.cleanup()

    def gravar_estado(self, base_onda=None):
        estado = f"Modo: alteração\nTestes travados: {self.sha_travado}\n"
        if base_onda:
            estado += f"- Base da onda: {base_onda}\n"
        (self.docs / "state.md").write_text(estado, encoding="utf-8")

    def rodar(self, *ids, onda=1):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = fo.main([str(self.docs), str(onda), *ids, "--repo", str(self.repo)])
        return codigo, saida.getvalue()

    def test_teste_liberado_pelo_plano_fecha_e_mostra_a_proxima(self):
        (self.repo / "tests" / "test_b.py").write_text("x = 2\n", encoding="utf-8")
        codigo, saida = self.rodar("BE-001", "FIX-ONDA1-1")
        self.assertEqual(codigo, 0, saida)
        self.assertEqual((self.docs / "feitos.txt").read_text(encoding="utf-8"), "BE-001\n")
        self.assertIn("1 liberado(s) pelo plano", saida)
        self.assertIn("fora do índice (não vão para feitos.txt): FIX-ONDA1-1", saida)
        self.assertIn("próxima: onda 2 (agent-map.json, suite completa): BE-002 forte", saida)
        self.assertLessEqual(len(saida.splitlines()), 8)

    def test_teste_travado_mudado_sem_aprovacao_nao_grava(self):
        (self.repo / "tests" / "test_a.py").write_text("x = 2\n", encoding="utf-8")
        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("tests/test_a.py", saida)
        self.assertFalse((self.docs / "feitos.txt").exists())

    def test_trava_respeita_onda_anterior_com_ou_sem_base_no_estado(self):
        self.gravar_estado(base_onda=self.sha_travado)
        teste = self.repo / "tests" / "test_b.py"
        teste.write_text("x = 2\n", encoding="utf-8")
        _git(self.repo, "add", "tests/test_b.py")
        _git(self.repo, "commit", "-qm", "ticket BE-001")
        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 0, saida)
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "scaffold(7): onda 1")
        base = _git(self.repo, "rev-parse", "HEAD")

        for base_no_estado in (None, base):
            with self.subTest(base_no_estado=base_no_estado):
                self.gravar_estado(base_onda=base_no_estado)
                codigo, saida = self.rodar("BE-002", onda=2)
                self.assertEqual(codigo, 0, saida)
                self.assertIn(f"trava: ok desde {base}", saida)

        teste.write_text("x = 3\n", encoding="utf-8")
        _git(self.repo, "add", "tests/test_b.py")
        _git(self.repo, "commit", "-qm", "mudança da onda 2")
        codigo, saida = self.rodar("BE-002", onda=2)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("tests/test_b.py", saida)

    def test_base_da_onda_nao_legitima_alteracao_anterior_sem_aprovacao(self):
        (self.repo / "tests" / "test_a.py").write_text("x = 2\n", encoding="utf-8")
        _git(self.repo, "add", "tests/test_a.py")
        _git(self.repo, "commit", "-qm", "alteração antes da primeira onda")
        self.gravar_estado(base_onda=_git(self.repo, "rev-parse", "HEAD"))
        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("tests/test_a.py", saida)

    def test_trava_com_nome_acentuado_em_arquivo_comitado(self):
        caminho = "tests/test_paginação.py"
        teste = self.repo / caminho
        teste.write_text("x = 1\n", encoding="utf-8")
        (self.docs / "testes-travados.txt").write_text(caminho + "\n", encoding="utf-8")
        _git(self.repo, "config", "core.quotePath", "true")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-qm", "teste de paginação na base")
        self.sha_travado = _git(self.repo, "rev-parse", "HEAD")
        self.gravar_estado()
        teste.write_text("x = 2\n", encoding="utf-8")

        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 1, saida)
        self.assertIn(caminho, saida)
        self.assertFalse((self.docs / "feitos.txt").exists())

    def test_ids_fora_da_onda_sao_erro_sem_gravar(self):
        for tid in ("BE-002", "BE-404"):
            with self.subTest(tid=tid):
                codigo, saida = self.rodar("BE-001", tid)
                self.assertEqual(codigo, 1, saida)
                self.assertIn(f"ids fora da onda 1 (agent-map.json): {tid}", saida)
                self.assertFalse((self.docs / "feitos.txt").exists())

    def test_fechamento_parcial_nao_avanca_e_pode_ser_retomado(self):
        mapa = {**MAPA, "ondas": [
            {**MAPA["ondas"][0], "tickets": [*MAPA["ondas"][0]["tickets"], {"id": "BE-003", "model": "medio"}]},
            MAPA["ondas"][1],
        ]}
        (self.docs / "agent-map.json").write_text(json.dumps(mapa), encoding="utf-8")
        teste = self.repo / "tests" / "test_b.py"
        teste.write_text("x = 2\n", encoding="utf-8")

        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("onda 1 incompleta", saida)
        self.assertFalse((self.docs / "feitos.txt").exists())
        for _ in range(2):
            codigo, saida = self.rodar("BE-001", "--parcial")
            self.assertEqual(codigo, 0, saida)
            self.assertIn("onda 1 parcial", saida)
            self.assertNotIn("próxima:", saida)
            self.assertEqual((self.docs / "feitos.txt").read_text(encoding="utf-8"), "BE-001\n")
        codigo, saida = self.rodar("BE-003")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("próxima: onda 2", saida)

    def test_worktree_de_subagente_que_ficou_nao_grava(self):
        _git(self.repo, "worktree", "add", "-q", "-b", "worktree-agent-x1", str(self.repo.parent / "agent-x1"))
        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 1, saida)
        self.assertIn("worktree-agent-x1", saida)
        self.assertFalse((self.docs / "feitos.txt").exists())

    def test_sem_feitos_depois_da_onda_1_recusa(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = fo.main([str(self.docs), "2", "BE-002", "--repo", str(self.repo)])
        self.assertEqual(codigo, 2, saida.getvalue())
        self.assertFalse((self.docs / "feitos.txt").exists())
        (self.docs / "feitos.txt").write_text("BE-001\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(fo.main([str(self.docs), "2", "BE-002", "--repo", str(self.repo)]), 0)
        self.assertEqual((self.docs / "feitos.txt").read_text(encoding="utf-8"), "BE-001\nBE-002\n")

    def test_replano_tem_prioridade_e_sem_trava_ainda(self):
        (self.docs / "state.md").write_text("Testes travados: ainda não\n", encoding="utf-8")
        replano = {"fonte": "scripts/ondas.py --feitos", "ondas": [
            {"onda": 2, "suite": "area", "tickets": [{"id": "BE-003", "model": "leve"}]}]}
        (self.docs / "ondas-replano.json").write_text(json.dumps(replano), encoding="utf-8")
        codigo, saida = self.rodar("BE-001")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("trava: sem testes travados ainda", saida)
        self.assertIn("próxima: onda 2 (ondas-replano.json, suite area): BE-003 leve", saida)

    def test_fim_do_replano_inclusive_vazio_nao_revive_mapa_original(self):
        for inicio, ondas_replano in ((1, [MAPA["ondas"][0]]), (2, [])):
            with self.subTest(inicio=inicio):
                replano = {"a_partir": inicio, "ondas": ondas_replano}
                (self.docs / "ondas-replano.json").write_text(json.dumps(replano), encoding="utf-8")
                codigo, saida = self.rodar("BE-001")
                self.assertEqual(codigo, 0, saida)
                self.assertIn("Fim de ondas-replano.json", saida)
                self.assertNotIn("BE-002", saida)
                codigo, saida = self.rodar("BE-002", onda=2)
                self.assertEqual(codigo, 1, saida)
                self.assertIn("não pertence ao plano ativo", saida)
                self.assertEqual((self.docs / "feitos.txt").read_text(encoding="utf-8"), "BE-001\n")


if __name__ == "__main__":
    unittest.main()
