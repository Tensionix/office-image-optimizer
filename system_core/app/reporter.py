from __future__ import annotations

from collections import Counter
from pathlib import Path

from .models import Mode, OptimizationPolicy, Preset, ProcessResult, ScanItem, ScanResult, policy_for_preset
from .rules import recommend


def _format_bytes(value: int) -> str:
    if value == 0:
        return "0 B"
    sign = "-" if value < 0 else ""
    units = ("B", "KB", "MB", "GB")
    size = float(abs(value))
    unit = units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    return f"{sign}{size:.1f} {unit}" if unit != "B" else f"{sign}{int(size)} B"


def _document_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _image_size_label(item: ScanItem) -> str:
    if not item.width or not item.height:
        return "unknown"
    return f"{item.width}x{item.height}"


def _scan_relevance_label(item_format: str) -> str:
    if item_format in {"jpg", "jpeg"}:
        return "SAFE+HARD"
    if item_format in {"png", "gif", "bmp", "tif", "tiff"}:
        return "HARD"
    return "UNSUPPORTED"


def render_scan_report(
    result: ScanResult,
    mode: Mode = "hard",
    preset: Preset = "uhd",
    batch: bool = False,
    analysis_label: str | None = None,
    policy: OptimizationPolicy | None = None,
) -> str:
    resolved_policy = policy or policy_for_preset(preset)
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("AUDION OFFICE IMAGE OPTIMIZER - ALPHA REPORT")
    lines.append("=" * 72)
    lines.append(f"Document      : {result.document_path}")
    lines.append(f"Package type  : {result.package_type}")
    lines.append(f"Document size : {_format_bytes(_document_size(result.document_path))}")
    if analysis_label:
        lines.append(f"Analysis mode : {analysis_label}")
    else:
        lines.append(f"Analysis mode : {mode.upper()} / {preset.upper()} / {'BATCH' if batch else 'ASK'}")
    lines.append(f"Policy        : {resolved_policy.limit_label}")
    lines.append("")

    if result.errors:
        lines.append("Errors:")
        for err in result.errors:
            lines.append(f"  - {err}")
        return "\n".join(lines)

    lines.append(f"Images found  : {result.total_images}")
    lines.append(f"Unsupported   : {result.unsupported_count}")
    lines.append(f"Media size    : {_format_bytes(sum(item.encoded_size_bytes for item in result.items))}")
    lines.append(f"Decoded est.  : {_format_bytes(sum(item.decoded_size_bytes_estimate for item in result.items))}")
    lines.append("")

    by_format = Counter(item.detected_format or "unknown" for item in result.items)
    bytes_by_format = Counter()
    for item in result.items:
        bytes_by_format[item.detected_format or "unknown"] += item.encoded_size_bytes
    if by_format:
        lines.append("Summary by format:")
        for key in sorted(by_format):
            lines.append(f"  - {key}: {by_format[key]} file(s), {_format_bytes(bytes_by_format[key])}")
        lines.append("")

    largest = sorted(result.items, key=lambda item: item.encoded_size_bytes, reverse=True)[:10]
    if largest:
        lines.append("Largest image parts:")
        for item in largest:
            lines.append(f"  - {_format_bytes(item.encoded_size_bytes):>9}  {_image_size_label(item):>22}  {item.package_path}")
        lines.append("")

    decisions = Counter()
    for index, item in enumerate(result.items, start=1):
        decision = recommend(item, mode=mode, preset=preset, batch=batch, policy=resolved_policy)
        decisions[decision.recommended_action] += 1
        transparency = "yes" if item.has_transparency else "no"
        lines.append(f"[{index:03d}] {item.package_path}")
        lines.append(f"      document      : {item.document_path}")
        lines.append(f"      format        : {item.detected_format or 'unknown'}")
        lines.append(f"      width         : {item.width if item.width else 'unknown'}")
        lines.append(f"      height        : {item.height if item.height else 'unknown'}")
        lines.append(f"      encoded size  : {_format_bytes(item.encoded_size_bytes)}")
        lines.append(f"      decoded est.  : {_format_bytes(item.decoded_size_bytes_estimate)}")
        lines.append(f"      transparency  : {transparency}")
        lines.append(f"      supported     : {'yes' if item.supported else 'no'}")
        lines.append(f"      relevance     : {_scan_relevance_label(item.detected_format)}")
        lines.append(f"      recommend     : {decision.recommended_action}")
        lines.append(f"      reason        : {decision.reason}")
        if item.note:
            lines.append(f"      note          : {item.note}")
        lines.append("")

    lines.append("Summary by recommendation:")
    for key in sorted(decisions):
        lines.append(f"  - {key}: {decisions[key]}")

    return "\n".join(lines)


def render_process_report(result: ProcessResult, analysis_label: str | None = None) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("AUDION OFFICE IMAGE OPTIMIZER - PROCESS REPORT")
    lines.append("=" * 72)
    lines.append(f"Document      : {result.document_path}")
    lines.append(f"Output        : {result.output_path}")
    lines.append(f"Package type  : {result.package_type}")
    if analysis_label:
        lines.append(f"Analysis mode : {analysis_label}")
    else:
        lines.append(f"Analysis mode : {result.mode.upper()} / {result.preset.upper()} / {'BATCH' if result.batch else 'ASK'}")
    lines.append("")

    if result.errors:
        lines.append("Errors:")
        for err in result.errors:
            lines.append(f"  - {err}")
        return "\n".join(lines)

    lines.append(f"Images found  : {result.total_images}")
    lines.append(f"Unsupported   : {result.unsupported_count}")
    lines.append(f"Input size    : {_format_bytes(result.input_size_bytes)}")
    lines.append(f"Output size   : {_format_bytes(result.output_size_bytes)}")
    if result.input_size_bytes and result.output_size_bytes:
        saved = result.input_size_bytes - result.output_size_bytes
        saved_percent = saved / result.input_size_bytes * 100
        size_delta_label = "Saved" if saved >= 0 else "Added"
        lines.append(f"{size_delta_label:<14}: {_format_bytes(abs(saved))} ({abs(saved_percent):.1f}%)")
    lines.append("")

    decisions = Counter()
    changed_count = 0
    for index, item in enumerate(result.items, start=1):
        transparency = "yes" if item.has_transparency else "no"
        if item.changed:
            changed_count += 1
        decisions[item.executed_action] += 1
        action_label = "selected" if not result.batch else "executed"
        lines.append(f"[{index:03d}] {item.package_path}")
        lines.append(f"      document      : {item.document_path}")
        lines.append(f"      format        : {item.detected_format or 'unknown'}")
        lines.append(f"      width         : {item.width if item.width else 'unknown'}")
        lines.append(f"      height        : {item.height if item.height else 'unknown'}")
        lines.append(f"      transparency  : {transparency}")
        lines.append(f"      recommend     : {item.recommended_action}")
        lines.append(f"      {action_label:<13}: {item.executed_action}")
        lines.append(f"      changed       : {'yes' if item.changed else 'no'}")
        lines.append(f"      size          : {_format_bytes(item.bytes_before)} -> {_format_bytes(item.bytes_after)}")
        if item.output_package_path != item.package_path:
            lines.append(f"      output part   : {item.output_package_path}")
        if item.note:
            lines.append(f"      note          : {item.note}")
        lines.append("")

    lines.append(f"Changed items : {changed_count}")
    if changed_count == 0:
        if result.mode == "safe":
            lines.append("No JPEG parts were changed.")
        else:
            lines.append("No image parts were changed.")
    lines.append("Summary by executed action:")
    for key in sorted(decisions):
        lines.append(f"  - {key}: {decisions[key]}")

    return "\n".join(lines)
