from __future__ import annotations

import re
import unittest
from pathlib import Path


MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class DocsIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.docs_root = cls.repo_root / "docs"
        cls.markdown_files = list(cls.docs_root.rglob("*.md"))

    def test_expected_docs_files_exist(self) -> None:
        expected_files = [
            "README.md",
            "_sidebar.md",
            "Modelagem/2.Modelagem.md",
            "Modelagem/2.1.ModelagemEstatica.md",
            "Modelagem/2.2.ModelagemDinamica.md",
            "Modelagem/2.3.ModelagemOrganizacionalCasosDeUso.md",
            "Projeto/Projeto.md",
        ]
        for relative_path in expected_files:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((self.docs_root / relative_path).exists())

    def test_sidebar_links_point_to_existing_files(self) -> None:
        sidebar_path = self.docs_root / "_sidebar.md"
        missing_targets: list[str] = []
        for link in self._extract_markdown_links(sidebar_path.read_text(encoding="utf-8")):
            if not link.startswith("/"):
                continue
            resolved = self._resolve_link(link, sidebar_path)
            if resolved is None or not resolved.exists():
                missing_targets.append(link)

        self.assertEqual([], missing_targets, f"Missing sidebar targets: {missing_targets}")

    def test_internal_markdown_links_are_valid(self) -> None:
        missing_targets: list[str] = []
        for markdown_file in self.markdown_files:
            content = markdown_file.read_text(encoding="utf-8")
            for link in self._extract_markdown_links(content):
                resolved = self._resolve_link(link, markdown_file)
                if resolved is None:
                    continue
                if not resolved.exists():
                    missing_targets.append(f"{markdown_file.relative_to(self.repo_root)} -> {link}")

        self.assertEqual([], missing_targets, f"Broken internal links: {missing_targets}")

    def _extract_markdown_links(self, content: str) -> list[str]:
        return [match.strip() for match in MARKDOWN_LINK_RE.findall(content)]

    def _resolve_link(self, link: str, source_file: Path) -> Path | None:
        normalized = link.split("#", 1)[0].split("?", 1)[0].strip()
        if not normalized or normalized.startswith(("http://", "https://", "mailto:")):
            return None
        if normalized == "/":
            return self.docs_root / "README.md"
        if normalized.startswith("/"):
            if normalized.startswith("/docs/"):
                normalized = normalized[len("/docs") :]
            target = self.docs_root / normalized.lstrip("/")
        else:
            target = source_file.parent / normalized
        return target.resolve()


if __name__ == "__main__":
    unittest.main()
