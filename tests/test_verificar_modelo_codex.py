import importlib.util
import pathlib
import unittest


SCRIPT = (
    pathlib.Path(__file__).parents[1]
    / "skills"
    / "molbytes-scaffold"
    / "scripts"
    / "verificar-modelo-codex.py"
)
SPEC = importlib.util.spec_from_file_location("verificar_modelo_codex", SCRIPT)
MODULO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULO)


class VerificarModeloCodexTests(unittest.TestCase):
    def test_resolve_modelo_padrao(self):
        resultado = MODULO.verificar(
            "scaffold-planner",
            "medio",
            "estágio 5",
            None,
            MODULO.modelos_configurados(None),
            estagio=5,
        )
        self.assertEqual("gpt-6.1-sol", resultado["modelo"])

    def test_recusa_nivel_incompativel_com_agente(self):
        with self.assertRaisesRegex(ValueError, "não aceita nível forte"):
            MODULO.verificar(
                "scaffold-router",
                "forte",
                "estágio 6",
                None,
                MODULO.modelos_configurados(None),
                estagio=6,
            )

    def test_recusa_nivel_abaixo_do_minimo(self):
        with self.assertRaisesRegex(ValueError, "exige no mínimo forte"):
            MODULO.verificar(
                "scaffold-security",
                "medio",
                "auditoria de segurança",
                None,
                MODULO.modelos_configurados(None),
                estagio=9,
            )

    def test_aceita_mapa_personalizado_completo(self):
        modelos = MODULO.modelos_configurados("leve=l,medio=m,forte=f")
        resultado = MODULO.verificar(
            "scaffold-implementer", "forte", "ticket crítico", "medio", modelos, estagio=7
        )
        self.assertEqual("f", resultado["modelo"])

    def test_recusa_mapa_personalizado_incompleto(self):
        with self.assertRaisesRegex(ValueError, "faltam níveis"):
            MODULO.modelos_configurados("leve=l,medio=m")

    def test_lote_distingue_disponibilidade_desconhecida_de_confirmada(self):
        lote = [{"agente": "scaffold-planner", "nivel": "medio", "tarefa": "tickets", "estagio": 5}]
        modelos = MODULO.modelos_configurados("leve=l,medio=m,forte=f")
        self.assertEqual(MODULO.verificar_lote(lote, modelos)[0]["disponibilidade"], "não verificada")
        with self.assertRaisesRegex(ValueError, "modelos ausentes no Codex: f"):
            MODULO.verificar_lote(lote, modelos, {"l", "m"})
        self.assertEqual(MODULO.verificar_lote(lote, modelos, {"l", "m", "f"})[0]["disponibilidade"], "confirmada")

    def test_lote_recusa_onda_inteira_se_uma_tarefa_for_invalida(self):
        lote = [
            {"agente": "scaffold-planner", "nivel": "medio", "tarefa": "tickets", "estagio": 5},
            {"agente": "scaffold-security", "nivel": "medio", "tarefa": "auditoria", "estagio": 9},
        ]
        with self.assertRaisesRegex(ValueError, "tarefa 2: a tarefa exige no mínimo forte"):
            MODULO.verificar_lote(lote, MODULO.MODELOS_PADRAO)


if __name__ == "__main__":
    unittest.main()
