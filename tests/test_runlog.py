"""Testes de skills/molbytes-scaffold/scripts/runlog.py.

    python -m unittest discover tests
"""
import importlib.util
import io
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("runlog", RAIZ / "skills" / "molbytes-scaffold" / "scripts" / "runlog.py")
runlog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runlog)

T0 = datetime(2026, 11, 7, 14, 5, 54, tzinfo=timezone.utc)
T1 = datetime(2026, 11, 7, 14, 19, 50, tzinfo=timezone.utc)
START = "2026-11-07T14:05:54+00:00 | START | scaffold-implementer | BE-091 | medio/sonnet | orçamento 25\n"


class TestLinhas(unittest.TestCase):
    def test_start_no_formato(self):
        linha = runlog.linha_start(T0, "scaffold-implementer", "BE-091", "medio/sonnet", "25")
        self.assertEqual(linha, START.strip())

    def test_start_recusa_orcamento_e_nivel_fora_do_formato(self):
        with self.assertRaises(ValueError):
            runlog.linha_start(T0, "scaffold-implementer", "BE-091", "medio/sonnet", "25 min")
        with self.assertRaises(ValueError):
            runlog.linha_start(T0, "scaffold-implementer", "BE-091", "sonnet", "25")

    def test_end_calcula_minutos_pelo_relogio_e_turnos_vao_na_nota(self):
        linha = runlog.linha_end(START, T1, "scaffold-implementer", "BE-091", "ok", tokens="206282", turnos="59")
        self.assertEqual(linha, "2026-11-07T14:19:50+00:00 | END | scaffold-implementer | BE-091 | ok | 14 | 206282 tokens | turnos 59")

    def test_end_recusa_status_fora_da_lista(self):
        with self.assertRaises(ValueError):
            runlog.linha_end(START, T1, "scaffold-implementer", "BE-091", "ok (2a corrida)")

    def test_end_sem_start_aberto_nao_grava(self):
        with self.assertRaises(LookupError):
            runlog.linha_end(START, T1, "scaffold-implementer", "BE-092", "ok")
        fechado = START + "2026-11-07T14:19:50+00:00 | END | scaffold-implementer | BE-091 | ok | 14 | ? tokens\n"
        with self.assertRaises(LookupError):
            runlog.linha_end(fechado, T1, "scaffold-implementer", "BE-091", "ok")

    def test_nota_nao_quebra_os_campos(self):
        linha = runlog.linha_end(START, T1, "scaffold-implementer", "BE-091", "parcial",
                                 nota="bateu o limite | VM a meio\ncontinuado")
        self.assertTrue(linha.endswith("| parcial | 14 | ? tokens | bateu o limite / VM a meio continuado"))
        self.assertEqual(len(linha.split("|")), 8)

    def test_abertos_pareia_pelo_mais_recente(self):
        log = (START
               + "2026-11-07T14:06:00+00:00 | START | scaffold-implementer | BE-092 | medio/sonnet | orçamento 15\n"
               + "2026-11-07T14:20:00+00:00 | END | scaffold-implementer | BE-091 | ok | 14 | ? tokens\n")
        self.assertEqual([s["ticket"] for s in runlog.abertos(log)], ["BE-092"])


class TestComando(unittest.TestCase):
    def rodar(self, *args):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = runlog.main(list(args))
        return codigo, saida.getvalue()

    def test_start_end_e_abertos_no_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertEqual(self.rodar(pasta, "start", "scaffold-planner", "estágio 5", "medio/sonnet", "15")[0], 0)
            codigo, texto = self.rodar(pasta, "abertos")
            self.assertEqual(codigo, 0)
            self.assertIn("estágio 5 | scaffold-planner | medio/sonnet", texto)
            self.assertEqual(self.rodar(pasta, "end", "scaffold-planner", "estágio 5", "ok", "--tokens", "120000")[0], 0)
            linhas = (pathlib.Path(pasta) / "runs.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(linhas), 2)
            self.assertRegex(linhas[1], r"\| END \| scaffold-planner \| estágio 5 \| ok \| \d+ \| 120000 tokens$")
            self.assertEqual(self.rodar(pasta, "abertos")[1], "")

    def test_erro_nao_grava(self):
        with tempfile.TemporaryDirectory() as pasta:
            codigo, texto = self.rodar(pasta, "end", "scaffold-planner", "estágio 5", "ok")
            self.assertEqual(codigo, 1)
            self.assertIn("Nada gravado", texto)
            self.assertFalse((pathlib.Path(pasta) / "runs.log").exists())


if __name__ == "__main__":
    unittest.main()
