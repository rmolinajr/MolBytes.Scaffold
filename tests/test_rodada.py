"""Exercita o estado de duas rodadas pelos comandos usados pela skill."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "molbytes-scaffold" / "scripts"
INDICE = """\
tickets:
- id: BE-001
  area: backend
  depende_de: []
  arquivos: [tests/test_cálculo.py]
  testes_alterados: [tests/test_cálculo.py]
- id: BE-002
  area: backend
  depende_de: [BE-001]
  arquivos: [src/calculo.py]
- id: FE-003
  area: frontend
  depende_de: [BE-002]
  arquivos: ["web/[empresa]/page.ts"]
"""
PECAS = """\
- id: FE-003A
  area: frontend
  depende_de: [BE-002]
  arquivos: ["web/[empresa]/page.ts"]
- id: FE-003B
  area: frontend
  depende_de: [FE-003A]
  arquivos: ["web/[empresa]/page.ts"]
"""


class RodadaDePontaAPonta(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.repo = Path(pasta.name)
        self.docs = self.repo / ".project"
        self.docs.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Scaffold Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.quotePath", "true")

    def git(self, *args):
        cmd = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(cmd.returncode, 0, cmd.stderr)
        return cmd.stdout.strip()

    def script(self, nome, *args, codigo=0):
        cmd = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(SCRIPTS / nome), str(self.docs), *args],
            cwd=self.repo,
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(cmd.returncode, codigo, cmd.stdout + cmd.stderr)
        return cmd.stdout

    def gravar(self, caminho, texto="exemplo\n"):
        arq = self.docs / caminho
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto, encoding="utf-8")

    def commit(self, mensagem):
        self.git("add", "-A")
        self.git("commit", "-qm", mensagem)
        return self.git("rev-parse", "HEAD")

    def planejar(self, indice):
        self.gravar("tickets.yaml", indice)
        classes = [
            {"id": tid, "model": "medio", "complexity": "media", "motivo": ""}
            for tid in ("BE-001", "BE-002", "FE-003")
        ]
        self.gravar("classificacao.json", json.dumps(classes))
        self.script("ondas.py")

    def test_aprovar_teste_replanejar_arquivar_e_reusar_ids(self):
        teste = self.repo / "tests" / "test_cálculo.py"
        teste.parent.mkdir()
        teste.write_text("valor = 1\n", encoding="utf-8")
        self.gravar("spec.md")
        self.gravar("testes-travados.txt", "tests/test_cálculo.py\n")
        self.gravar("testes-intermitentes.txt")
        self.gravar("runs-orquestrador.sessao-a.jsonl", "{}\n")
        self.gravar("testes-liberados.txt")
        self.planejar(INDICE)
        base = self.commit("base")

        def estado(onda, inicio):
            self.gravar(
                "state.md",
                f"Fase: fase1\nModo: alteração (base_commit {base})\n"
                f"Testes travados: {base}\nOnda atual: {onda} de 4\nBase da onda: {inicio}\n",
            )

        estado(1, base)
        self.script("runlog.py", "start", "scaffold-implementer", "BE-001", "medio/sonnet", "15")
        teste.write_text("valor = 2\n", encoding="utf-8")
        self.script("runlog.py", "end", "scaffold-implementer", "BE-001", "ok", "--tokens", "1200")
        self.script("fechar-onda.py", "1", "BE-001")
        inicio = self.commit("scaffold(7): onda 1")

        estado(2, inicio)
        codigo = self.repo / "src" / "calculo.py"
        codigo.parent.mkdir()
        codigo.write_text("valor = 2\n", encoding="utf-8")
        self.script("fechar-onda.py", "2", "BE-002")
        inicio = self.commit("scaffold(7): onda 2")

        self.gravar("tickets.yaml", INDICE + PECAS)
        self.script("ondas.py", "--feitos", str(self.docs / "feitos.txt"), "--a-partir", "3")
        estado(3, inicio)
        self.assertIn("FE-003B", self.script("fechar-onda.py", "3", "FE-003A"))
        inicio = self.commit("scaffold(7): onda 3")
        estado(4, inicio)
        self.script("fechar-onda.py", "4", "FE-003B")
        self.gravar("state.md", "Fase: fase1\n- [x] 11 final\n")

        self.script("arquivar-rodada.py", "fase1", "--extra", "testes-liberados.txt")
        fase = self.docs / "fase1"
        for nome in ("state.md", "feitos.txt", "ondas-replano.json", "runs.log",
                     "testes-intermitentes.txt", "testes-liberados.txt", "runs-orquestrador.sessao-a.jsonl"):
            self.assertFalse((self.docs / nome).exists(), nome)
            self.assertTrue((fase / nome).is_file(), nome)
        self.assertTrue((self.docs / "spec.md").is_file())

        self.planejar(INDICE)
        self.script("fechar-onda.py", "1", "BE-001")
        self.assertEqual((self.docs / "feitos.txt").read_text(encoding="utf-8"), "BE-001\n")

    def test_arquivamento_valida_antes_de_mover(self):
        self.gravar("state.md")
        self.gravar("fase1/feitos.txt", "anterior\n")
        self.script("arquivar-rodada.py", "fase1", codigo=1)
        self.script("arquivar-rodada.py", "fase2", "--extra", "../outro.md", codigo=1)
        self.assertTrue((self.docs / "state.md").is_file())
        self.assertEqual((self.docs / "fase1/feitos.txt").read_text(encoding="utf-8"), "anterior\n")


if __name__ == "__main__":
    unittest.main()
