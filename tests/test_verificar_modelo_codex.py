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
            )

    def test_recusa_nivel_abaixo_do_minimo(self):
        with self.assertRaisesRegex(ValueError, "exige no mínimo forte"):
            MODULO.verificar(
                "scaffold-security",
                "medio",
                "auditoria de segurança",
                "forte",
                MODULO.modelos_configurados(None),
            )

    def test_aceita_mapa_personalizado_completo(self):
        modelos = MODULO.modelos_configurados("leve=l,medio=m,forte=f")
        resultado = MODULO.verificar(
            "scaffold-implementer", "forte", "ticket crítico", "medio", modelos
        )
        self.assertEqual("f", resultado["modelo"])

    def test_recusa_mapa_personalizado_incompleto(self):
        with self.assertRaisesRegex(ValueError, "faltam níveis"):
            MODULO.modelos_configurados("leve=l,medio=m")


if __name__ == "__main__":
    unittest.main()
