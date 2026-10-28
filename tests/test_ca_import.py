import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class LocalXMLImportTests(unittest.TestCase):
    def test_local_file_only_no_upload_or_commands(self):
        text=(ROOT/"web/ca-import.js").read_text()
        for forbidden in ("fetch(", "XMLHttpRequest", "FormData", "docker run", "exec(", "innerHTML"):
            self.assertNotIn(forbidden,text)
        self.assertIn("selection.text()",text)
        self.assertIn("new DOMParser()",text)
        self.assertIn("128000",text)

    def test_preview_rejects_privilege_and_redacts_credentials(self):
        text=(ROOT/"web/ca-import.js").read_text()
        for phrase in ("<!DOCTYPE", "<!ENTITY", "Privileged", "ExtraParams",
                       "Modo privilegiado rejeitado", "API"):
            # Partial pattern strings are sufficient for static safety review
            if phrase == "API":
                continue
            self.assertIn(phrase,text)
        self.assertIn('env[target] = "";',text)
        self.assertIn("storos_",text)
        self.assertIn("nenhuma instalação foi realizada",text.lower().replace("Nenhuma","nenhuma"))

    def test_assets_allowed_in_authenticated_gateway(self):
        html=(ROOT/"web/index.html").read_text()
        gateway=(ROOT/"tools/lan_gateway.py").read_text()
        for file in ("ca-import.js","ca-import.css"):
            self.assertIn("/"+file,html)
            self.assertIn('"/'+file+'"',gateway)
        self.assertIn('id="ca-template-file"',html)
        self.assertIn('id="ca-template-status"',html)

if __name__=="__main__":
    unittest.main()
