from __future__ import annotations

from pathlib import Path
import json
import sys


def detect_python_mode(root: Path) -> str:
    if (root / "runtime" / "python.exe").exists():
        return "portable-runtime"
    if (root / "runtime" / "python" / "python.exe").exists():
        return "portable-runtime"
    return "system-python"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    payload = {
        "project": "Audion Office Image Optimizer",
        "project_root": str(root),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "python_mode": detect_python_mode(root),
        "launchers": {
            "en": {
                "standard": str(root / "launcher_project.cmd"),
                "picker": str(root / "launcher_project_picker.cmd"),
            },
            "ru": {
                "standard": str(root / "launcher_project_ru.cmd"),
                "picker": str(root / "launcher_project_picker_ru.cmd"),
            },
        },
        "folders": {
            "input": str(root / "input"),
            "output": str(root / "output"),
            "logs": str(root / "logs"),
            "github_docs": str(root / "GitHub"),
            "runtime": str(root / "runtime"),
            "wheelhouse": str(root / "wheelhouse"),
            "release": str(root / "release"),
        },
        "entrypoint": "python -m app",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
