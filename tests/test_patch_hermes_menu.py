import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("patch_menu", Path(__file__).parents[1] / "tools/patch_hermes_menu.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class MenuPatchTests(unittest.TestCase):
    def collector(self):
        source = ('def collect(platform, skill_triples, core, plugins, limit):\n'
                  + p.ANCHOR
                  + '    entries = core + plugins + skill_triples\n'
                  + '    return entries[:limit]\n')
        scope = {}
        exec(p.transform(source), scope)
        return scope["collect"]

    def test_overflow_preserves_core_plugins_and_zion(self):
        collect = self.collector()
        skills = [(f"a{i:03}", "skill", f"/a{i:03}") for i in range(150)] + [("zion", "Zion", "/zion")]
        core = [("help", "Help", ""), ("cancel", "Cancel", "")]
        plugin = [("plugin", "Plugin", "")]
        result = collect("telegram", skills, core, plugin, 100)
        self.assertEqual(len(result), 100)
        self.assertEqual(result[:4], core + plugin + [("zion", "Zion", "/zion")])
        self.assertEqual(result[4:], [(f"a{i:03}", "skill", f"/a{i:03}") for i in range(96)])

    def test_other_platforms_and_missing_or_disabled_zion_are_unchanged(self):
        collect = self.collector()
        skills = [("alpha", "A", "/alpha"), ("zion", "Z", "/zion")]
        self.assertEqual(collect("discord", skills[:], [], [], 1), skills[:1])
        self.assertEqual(collect("telegram", skills[:1], [], [], 100), skills[:1])

    def test_idempotent_and_unknown_layout_refused(self):
        source = "def original():\n" + p.ANCHOR + "    pass\n"
        once = p.transform(source)
        self.assertEqual(p.transform(once), once)
        with self.assertRaisesRegex(ValueError, "collector changed"):
            p.transform("def newer():\n    pass\n")


if __name__ == "__main__":
    unittest.main()
