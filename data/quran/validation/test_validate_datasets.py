import unittest
from xml.etree import ElementTree as ET

from validate_datasets import metadata_sections


class MetadataNamespaceTests(unittest.TestCase):
    def test_reads_sections_from_namespaced_metadata(self):
        root = ET.fromstring(
            '<quran xmlns="https://tanzil.net/docs/Quran_Metadata">'
            '<suras><sura index="1" /></suras>'
            '<pages><page index="1" /></pages>'
            '</quran>'
        )

        sections = metadata_sections(root)

        self.assertEqual(set(sections), {"suras", "pages"})
        self.assertEqual(sections["suras"][0].get("index"), "1")
        self.assertEqual(sections["pages"][0].get("index"), "1")

    def test_reads_sections_from_unnamespaced_metadata(self):
        root = ET.fromstring('<quran><suras><sura index="1" /></suras></quran>')

        self.assertIn("suras", metadata_sections(root))


if __name__ == "__main__":
    unittest.main()
