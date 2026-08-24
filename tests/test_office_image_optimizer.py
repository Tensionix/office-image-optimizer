from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zipfile import ZIP_DEFLATED, ZipFile
import sys
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system_core.app.ooxml_package import (
    write_hard_batch_document,
    write_profile_normalized_document,
)
from system_core.app.scanner import scan_document
from system_core.core.jobs import execute_operation
from system_core.core.manifest import Operation
from system_core.core.paths import get_project_paths


REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
SERVICE = "system_core.services.image_optimizer_service:run_cli_for_input"


def _image_bytes(fmt: str, size: tuple[int, int], color: tuple[int, ...]) -> bytes:
    mode = "RGBA" if len(color) == 4 else "RGB"
    image = Image.new(mode, size, color)
    output = BytesIO()
    image.save(output, format=fmt)
    return output.getvalue()


def _sample_package(path: Path, package_type: str) -> None:
    if package_type == "docx":
        prefix = "word"
        document_part = "word/document.xml"
        rels_part = "word/_rels/document.xml.rels"
        main_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
        root_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    else:
        prefix = "ppt"
        document_part = "ppt/presentation.xml"
        rels_part = "ppt/_rels/presentation.xml.rels"
        main_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
        root_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"

    content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CONTENT_TYPES_NS}">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="jpg" ContentType="image/jpeg"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Override PartName="/{document_part}" ContentType="{main_type}"/>
</Types>"""
    root_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Id="rId1" Type="{root_type}" Target="{document_part}"/>
</Relationships>"""
    document_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Id="rIdImage1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/photo.jpg"/>
  <Relationship Id="rIdImage2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/alpha.png"/>
  <Relationship Id="rIdImage3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/vector.svg"/>
</Relationships>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr(document_part, "<?xml version='1.0' encoding='UTF-8'?><root/>")
        archive.writestr(rels_part, document_rels)
        archive.writestr(f"{prefix}/media/photo.jpg", _image_bytes("JPEG", (2400, 1600), (80, 120, 180)))
        archive.writestr(f"{prefix}/media/alpha.png", _image_bytes("PNG", (720, 520), (180, 60, 40, 170)))
        archive.writestr(f"{prefix}/media/vector.svg", b"<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'/>")


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


class OfficeImageOptimizerTests(TestCase):
    def test_scanner_recognizes_docx_and_pptx_without_modifying_sources(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for package_type in ("docx", "pptx"):
                source = root / f"sample.{package_type}"
                _sample_package(source, package_type)
                before = _digest(source)
                result = scan_document(source)
                self.assertEqual(result.errors, [])
                self.assertEqual(result.package_type, package_type)
                self.assertEqual(result.total_images, 3)
                self.assertEqual({item.detected_format for item in result.items}, {"jpeg", "png", "svg"})
                self.assertEqual(result.unsupported_count, 1)
                self.assertEqual(_digest(source), before)

    def test_hard_batch_rewrites_raster_relationships_and_preserves_vector(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.docx"
            output = root / "output"
            _sample_package(source, "docx")
            before = _digest(source)

            result = write_hard_batch_document(source, "fhd", output_dir=output)

            self.assertEqual(result.errors, [])
            self.assertTrue(result.output_path.exists())
            self.assertEqual(_digest(source), before)
            with ZipFile(result.output_path) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertIn("word/media/alpha.jpg", names)
                self.assertNotIn("word/media/alpha.png", names)
                self.assertIn("word/media/vector.svg", names)
                rels = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
                targets = {node.get("Target") for node in rels.findall(f"{{{REL_NS}}}Relationship")}
                self.assertIn("media/alpha.jpg", targets)
                self.assertNotIn("media/alpha.png", targets)
                types = ET.fromstring(archive.read("[Content_Types].xml"))
                defaults = {
                    node.get("Extension"): node.get("ContentType")
                    for node in types.findall(f"{{{CONTENT_TYPES_NS}}}Default")
                }
                self.assertEqual(defaults.get("jpg"), "image/jpeg")

    def test_srgb_and_cmyk_normalization_produce_readable_packages(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.pptx"
            _sample_package(source, "pptx")
            before = _digest(source)

            for mode in ("normalize-srgb", "normalize-cmyk"):
                target = root / mode
                result = write_profile_normalized_document(source, profile_mode=mode, output_dir=target)
                self.assertEqual(result.errors, [])
                self.assertTrue(result.output_path.exists())
                with ZipFile(result.output_path) as archive:
                    self.assertIsNone(archive.testzip())
                    self.assertIn("ppt/media/vector.svg", archive.namelist())

            self.assertEqual(_digest(source), before)

    def test_workbench_paths_drive_every_gui_backend_operation(self) -> None:
        with TemporaryDirectory() as directory:
            temp = Path(directory)
            source = temp / "selected-source.docx"
            _sample_package(source, "docx")
            source_digest = _digest(source)
            base_paths = get_project_paths(Path(__file__).resolve().parents[1])

            cases = [
                ("scan", {}),
                ("ask", {"mode": "hard", "preset": "presentation"}),
                ("batch", {"mode": "hard", "preset": "fhd"}),
                ("fit-size", {"target_mb": 1}),
                ("normalize-srgb", {}),
                ("normalize-cmyk", {}),
                ("extract-media", {}),
            ]
            for command, extra in cases:
                output = temp / f"output-{command}"
                logs = temp / f"logs-{command}"
                reports = temp / f"reports-{command}"
                paths = replace(base_paths, input=source, output=output, logs=logs, report=reports)
                operation = Operation(
                    id=f"test_{command}",
                    title=command,
                    description="",
                    service=SERVICE,
                    parameters={"command": command, **extra},
                )
                result = execute_operation(paths, operation)
                self.assertTrue(result.ok, result.message)
                self.assertEqual(_digest(source), source_digest)

                if command in {"batch", "fit-size", "normalize-srgb", "normalize-cmyk"}:
                    produced = output / "selected-source.optimized.docx"
                    self.assertTrue(produced.exists(), f"{command} did not use Workbench TARGET")
                    with ZipFile(produced) as archive:
                        self.assertIsNone(archive.testzip())
                elif command == "extract-media":
                    extracted = output / "selected-source"
                    self.assertTrue((extracted / "photo.jpg").exists())
                    self.assertTrue((extracted / "alpha.png").exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
