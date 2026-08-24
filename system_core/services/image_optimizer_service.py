from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import os
import re
import shutil

from system_core.core.jobs import JobContext, resolve_project_path, run_process


OFFICE_EXTENSIONS = {".docx", ".pptx"}
MEDIA_PREFIXES = ("word/media/", "ppt/media/")


COMMANDS_WITH_OUTPUT = {"ask", "batch", "fit-size", "normalize-srgb", "normalize-cmyk", "extract-media"}
COMMANDS_WITH_MODE_PRESET = {"scan", "ask", "batch"}
COMMANDS_WITH_OPTIMIZATION_POLICY = {"scan", "ask", "batch"}
OPTIMIZATION_PARAMETER_FLAGS = {
    "max_width": "--max-width",
    "max_height": "--max-height",
    "max_megapixels": "--max-megapixels",
    "jpeg_quality": "--jpeg-quality",
    "min_skip_width": "--min-skip-width",
    "min_skip_height": "--min-skip-height",
    "min_skip_megapixels": "--min-skip-megapixels",
}
FIT_SIZE_PARAMETER_FLAGS = {
    "target_mb": "--target-mb",
}

SIZE_LIMIT_PRESETS = {
    "fhd": (1920, 1080),
    "fullhd": (1920, 1080),
    "full hd": (1920, 1080),
    "1080p": (1920, 1080),
    "qhd": (2560, 1440),
    "2k": (2560, 1440),
    "1440p": (2560, 1440),
    "uhd": (3840, 2160),
    "4k": (3840, 2160),
    "2160p": (3840, 2160),
}


def _parameter_text(context: JobContext, key: str) -> str:
    value = context.operation.parameters.get(key)
    return str(value or "").strip()


def _input_source(context: JobContext) -> Path:
    raw_path = _parameter_text(context, "input_path")
    if raw_path:
        return resolve_project_path(context, raw_path)
    return context.paths.input


def _output_root(context: JobContext) -> Path:
    raw_path = _parameter_text(context, "output_path")
    if raw_path:
        return resolve_project_path(context, raw_path)
    context.paths.output.mkdir(parents=True, exist_ok=True)
    return context.paths.output


def _append_if_present(command: list[str], flag: str, value: object) -> None:
    if value in {"", None}:
        return
    command.extend([flag, str(value)])


def _parse_image_limit(value: object) -> tuple[int | None, int | None]:
    text = str(value or "").strip()
    if not text:
        return None, None

    normalized = text.lower()
    normalized = normalized.replace("×", "x").replace("*", "x").replace("х", "x")
    normalized = re.sub(r"\s+", " ", normalized)
    preset_key = normalized.replace("-", " ").strip()
    if preset_key in SIZE_LIMIT_PRESETS:
        return SIZE_LIMIT_PRESETS[preset_key]

    size_match = re.search(r"(?<!\d)(\d{3,5})\s*x\s*(\d{3,5})(?!\d)", normalized)
    width = int(size_match.group(1)) if size_match else None
    height = int(size_match.group(2)) if size_match else None

    if width is None and height is None:
        raise RuntimeError(
            f"Could not parse image limit: {text}. Use examples like 1920x1080 or 4K."
        )

    return width, height


MIN_CUSTOM_RESOLUTION = 400
CUSTOM_RESOLUTION_ERROR = "Необходимо ввести не менее 400x400 px"
CUSTOM_MODES = {"safe", "hard"}


def _parse_positive_integer(value: object, label: str, minimum: int = 1) -> int | None:
    if value in {"", None}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{label} must be a number.") from exc
    if parsed < minimum:
        raise RuntimeError(CUSTOM_RESOLUTION_ERROR if minimum >= MIN_CUSTOM_RESOLUTION else f"{label} must be greater than 0.")
    return parsed


def _parse_jpeg_quality(value: object) -> int | None:
    if value in {"", None}:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("JPEG quality must be a number.") from exc
    return max(40, min(95, parsed))


def _area_limit(width: int | None, height: int | None) -> float | None:
    if width is None or height is None:
        return None
    return round((width * height) / 1_000_000, 2)


def _apply_image_limit_parameters(parameters: dict[str, object]) -> None:
    resolution_mode = str(parameters.get("resolution_mode") or "preset").strip().lower()
    jpeg_quality = _parse_jpeg_quality(parameters.get("jpeg_quality"))
    if jpeg_quality is not None:
        parameters["jpeg_quality"] = jpeg_quality
    if resolution_mode == "custom":
        width = _parse_positive_integer(parameters.get("custom_width"), "Custom width", MIN_CUSTOM_RESOLUTION)
        height = _parse_positive_integer(parameters.get("custom_height"), "Custom height", MIN_CUSTOM_RESOLUTION)
        if width is None or height is None:
            raise RuntimeError(CUSTOM_RESOLUTION_ERROR)
        custom_mode = str(parameters.get("expert_mode") or "hard").strip().lower()
        parameters["mode"] = custom_mode if custom_mode in CUSTOM_MODES else "hard"
    else:
        parameters["mode"] = "hard"
        image_limit = parameters.get("image_limit")
        if image_limit in {"", None}:
            return
        width, height = _parse_image_limit(image_limit)

    if width is not None:
        parameters["max_width"] = width
    if height is not None:
        parameters["max_height"] = height
    area_limit = _area_limit(width, height)
    if area_limit is not None:
        parameters["max_megapixels"] = area_limit
    skip_width = _parse_positive_integer(parameters.get("min_skip_width"), "Tiny image width", 0)
    skip_height = _parse_positive_integer(parameters.get("min_skip_height"), "Tiny image height", 0)
    skip_area_limit = _area_limit(skip_width, skip_height)
    if skip_area_limit is not None:
        parameters["min_skip_megapixels"] = max(0.01, skip_area_limit)


def _resolved_parameters(context: JobContext) -> dict[str, object]:
    parameters = dict(context.operation.parameters)
    _apply_image_limit_parameters(parameters)
    return parameters


def _input_documents(context: JobContext) -> list[Path]:
    source = _input_source(context)
    context.log(f"Input path: {source}")
    if source.is_file():
        if source.suffix.lower() not in OFFICE_EXTENSIONS:
            raise RuntimeError(f"Input file must be DOCX/PPTX: {source}")
        return [source]
    if not source.exists():
        raise RuntimeError(f"Input path does not exist: {source}")
    if not source.is_dir():
        raise RuntimeError(f"Input path is not a file or folder: {source}")
    return sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in OFFICE_EXTENSIONS
    )


def _python_exe(context: JobContext) -> Path:
    candidates = [
        context.paths.root / "runtime" / "python.exe",
        context.paths.root / "runtime" / "python" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("Portable Python runtime was not found. Build the Env first.")


def _run_subprocess(context: JobContext, command: list[str]) -> int:
    result = run_process(
        context,
        command,
        cwd=context.paths.root,
        extra_env={"PYTHONPATH": "system_core"},
        check=False,
        progress_seconds=120.0,
    )
    return result.exit_code


def run_doctor(context: JobContext) -> dict[str, object]:
    doctor_script = context.paths.system_core / "doctor.py"
    if not doctor_script.exists():
        raise RuntimeError(f"Doctor script was not found: {doctor_script}")
    python_exe = _python_exe(context)
    result = run_process(
        context,
        [str(python_exe), str(doctor_script)],
        cwd=context.paths.root,
        extra_env={"PYTHONPATH": "system_core"},
        check=False,
        progress_seconds=30.0,
    )
    context.progress(1.0)
    if result.exit_code != 0:
        raise RuntimeError(f"Doctor failed with exit code {result.exit_code}.")
    return {"exit_code": result.exit_code}


def run_cli_for_input(context: JobContext) -> dict[str, object]:
    documents = _input_documents(context)
    if not documents:
        context.log("No DOCX/PPTX files found in input.")
        context.progress(1.0)
        return {"processed": 0, "errors": 0}

    parameters = _resolved_parameters(context)
    command_name = str(parameters.get("command", "")).strip()
    mode = str(parameters.get("mode", "")).strip()
    preset = str(parameters.get("preset", "")).strip()
    embed_icc = bool(parameters.get("embed_icc", False))
    output_root = _output_root(context)
    if not command_name:
        raise RuntimeError("Missing operation parameter: command")
    if output_root and command_name not in COMMANDS_WITH_OUTPUT:
        context.log(f"[INFO] Output path is ignored by command: {command_name}")

    python_exe = _python_exe(context)
    failures = 0
    for index, document in enumerate(documents, start=1):
        if context.cancelled():
            context.log("Operation cancelled by user.")
            return {"processed": index - 1, "errors": failures, "cancelled": True}

        context.log("=" * 72)
        context.log(f"[{index}/{len(documents)}] {document}")
        command = [str(python_exe), "-m", "app", command_name, str(document)]
        if mode and command_name in COMMANDS_WITH_MODE_PRESET:
            command.extend(["--mode", mode])
        if preset and command_name in COMMANDS_WITH_MODE_PRESET:
            command.extend(["--preset", preset])
        if embed_icc:
            command.append("--embed-icc")
        if output_root and command_name in COMMANDS_WITH_OUTPUT:
            command.extend(["--out", str(output_root)])
        if command_name in COMMANDS_WITH_OPTIMIZATION_POLICY:
            for parameter_name, flag in OPTIMIZATION_PARAMETER_FLAGS.items():
                _append_if_present(command, flag, parameters.get(parameter_name))
        if command_name == "fit-size":
            for parameter_name, flag in FIT_SIZE_PARAMETER_FLAGS.items():
                _append_if_present(command, flag, parameters.get(parameter_name))

        rc = _run_subprocess(context, command)
        if rc != 0:
            failures += 1
            context.log(f"[ERROR] Command failed with exit code {rc}: {document.name}")
        context.progress(index / max(1, len(documents)))

    if failures:
        raise RuntimeError(f"Completed with {failures} failed file(s).")
    return {"processed": len(documents), "errors": 0}


def extract_media_from_input(context: JobContext) -> dict[str, object]:
    documents = _input_documents(context)
    if not documents:
        context.log("No DOCX/PPTX files found in input.")
        context.progress(1.0)
        return {"processed": 0, "extracted": 0}

    output_root = _output_root(context) or context.paths.output
    output_root.mkdir(parents=True, exist_ok=True)
    total_extracted = 0
    for index, document in enumerate(documents, start=1):
        if context.cancelled():
            context.log("Operation cancelled by user.")
            return {"processed": index - 1, "extracted": total_extracted, "cancelled": True}

        target_dir = output_root / document.stem
        target_dir.mkdir(parents=True, exist_ok=True)
        extracted_for_document = 0
        context.log("=" * 72)
        context.log(f"[{index}/{len(documents)}] Extract media: {document.name}")
        context.log(f"Target folder: {target_dir}")

        with ZipFile(document, "r") as archive:
            media_names = [
                name
                for name in archive.namelist()
                if not name.endswith("/") and name.lower().startswith(MEDIA_PREFIXES)
            ]
            for media_name in media_names:
                source_name = Path(media_name).name
                target_path = target_dir / source_name
                with archive.open(media_name) as source, target_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                extracted_for_document += 1
                total_extracted += 1
                context.log(f"EXTRACTED: {media_name} -> {target_path.name}")

        if extracted_for_document == 0:
            context.log("No word/media or ppt/media image parts found.")
        else:
            context.log(f"Extracted media files: {extracted_for_document}")
        context.progress(index / max(1, len(documents)))

    return {"processed": len(documents), "extracted": total_extracted}


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child_resolved = str(child.resolve())
        parent_resolved = str(parent.resolve())
        return os.path.commonpath([child_resolved, parent_resolved]) == parent_resolved
    except (OSError, ValueError):
        return False


def _clean_managed_folder(context: JobContext, folder: Path, label: str) -> dict[str, object]:
    root = context.paths.root.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    folder_resolved = folder.resolve()
    if folder.is_symlink() or not _is_inside(folder_resolved, root):
        raise RuntimeError(f"{label} cleanup blocked for safety.")

    removed = 0
    skipped: list[str] = []
    for item in folder.iterdir():
        if item.name == ".gitkeep":
            continue
        try:
            if item.is_symlink() or item.is_file():
                item.unlink()
            elif item.is_dir() and _is_inside(item, folder_resolved):
                shutil.rmtree(item)
            else:
                skipped.append(item.name)
                continue
            removed += 1
            context.log(f"Removed from {label}: {item.name}")
        except OSError as exc:
            skipped.append(f"{item.name} ({exc})")
    return {"removed_items": removed, "skipped_items": skipped}


def cleanup_input_output(context: JobContext) -> dict[str, object]:
    context.log("Cleaning managed input/output folders.")
    input_result = _clean_managed_folder(context, context.paths.input, "input")
    context.progress(0.5)
    output_result = _clean_managed_folder(context, context.paths.output, "output")
    context.progress(1.0)
    return {"input": input_result, "output": output_result}
