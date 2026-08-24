from __future__ import annotations

import argparse
import sys

from .models import Action, Mode, PRESET_POLICIES, OptimizationPolicy, Preset, build_optimization_policy
from .media_extract import extract_media, render_media_extract_report
from .ooxml_package import write_fit_size_document, write_hard_batch_document, write_profile_normalized_document, write_safe_document
from .reporter import render_process_report, render_scan_report
from .scanner import scan_document
from .rules import recommend


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _format_bytes(value: int) -> str:
    if value == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB")
    size = float(abs(value))
    unit = units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    sign = "-" if value < 0 else ""
    return f"{sign}{size:.1f} {unit}" if unit != "B" else f"{sign}{int(size)} B"


def _add_common_mode_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", help="Path to a DOCX or PPTX file")
    parser.add_argument("--mode", choices=("safe", "hard"), default="hard")
    parser.add_argument("--preset", choices=tuple(PRESET_POLICIES), default="presentation")
    parser.add_argument("--max-width", type=int, default=None, help="Custom maximum image width in pixels.")
    parser.add_argument("--max-height", type=int, default=None, help="Custom maximum image height in pixels.")
    parser.add_argument("--max-megapixels", type=float, default=None, help="Custom maximum decoded image megapixels.")
    parser.add_argument("--jpeg-quality", type=int, default=None, help="Custom JPEG quality, 40-95.")
    parser.add_argument("--min-skip-width", type=int, default=None, help="Skip tiny images only when width is at or below this value.")
    parser.add_argument("--min-skip-height", type=int, default=None, help="Skip tiny images only when height is at or below this value.")
    parser.add_argument("--min-skip-megapixels", type=float, default=None, help="Skip tiny images only when megapixels are at or below this value.")
    parser.add_argument("--out", default=None, help="Output folder. Defaults to project output folder.")


def _optimization_policy_from_args(args: argparse.Namespace) -> OptimizationPolicy:
    return build_optimization_policy(
        str(getattr(args, "preset", "presentation")),
        max_width=getattr(args, "max_width", None),
        max_height=getattr(args, "max_height", None),
        max_megapixels=getattr(args, "max_megapixels", None),
        jpeg_quality=getattr(args, "jpeg_quality", None),
        min_skip_width=getattr(args, "min_skip_width", None),
        min_skip_height=getattr(args, "min_skip_height", None),
        min_skip_megapixels=getattr(args, "min_skip_megapixels", None),
    )


SAFE_ACTION_OPTIONS: list[tuple[str, Action, str]] = [
    ("1", "keep", "keep"),
    ("2", "recompress", "recompress"),
    ("3", "resize", "resize"),
    ("4", "resize+recompress", "resize + recompress"),
    ("5", "skip", "skip"),
]


def _safe_similarity_key(package_type: str, package_path: str, recommended_action: Action) -> str:
    suffix = package_path.rsplit("/", 1)[-1].rsplit(".", 1)[-1].lower()
    return f"{package_type}:{suffix}:{recommended_action}"


def _prompt_safe_actions(target: str, preset: Preset, policy: OptimizationPolicy) -> dict[str, Action]:
    scan_result = scan_document(target)
    if scan_result.errors:
        return {}

    selected_actions: dict[str, Action] = {}
    apply_to_similar: dict[str, Action] = {}
    jpeg_items = [item for item in scan_result.items if item.detected_format in {"jpg", "jpeg"}]

    if not jpeg_items:
        print("[INFO] No JPEG image parts found for SAFE interactive actions.")
        return selected_actions

    print("=" * 72)
    print("SAFE ASK - JPEG ACTION SELECTION")
    print("=" * 72)
    print("Choose an action for each JPEG image part.")
    print("Use 1-5 to select an action. After selection, you can apply it to all similar JPEGs.")
    print("")

    for index, item in enumerate(jpeg_items, start=1):
        decision = recommend(item, mode="safe", preset=preset, batch=False, policy=policy)
        similarity_key = _safe_similarity_key(scan_result.package_type, item.package_path, decision.recommended_action)
        if similarity_key in apply_to_similar:
            selected_actions[item.package_path] = apply_to_similar[similarity_key]
            continue

        dims = f"{item.width}x{item.height}" if item.width and item.height else "unknown"
        print(f"[{index:03d}] {item.package_path}")
        print(f"  format       : {item.detected_format}")
        print(f"  size         : {dims}")
        print(f"  recommended  : {decision.recommended_action}")
        print(f"  reason       : {decision.reason}")
        print("  actions      : 1=keep  2=recompress  3=resize  4=resize+recompress  5=skip")

        chosen_action: Action | None = None
        while chosen_action is None:
            raw = input("  Select action [1-5]: ").strip().lower()
            for option_key, option_action, _label in SAFE_ACTION_OPTIONS:
                if raw == option_key:
                    chosen_action = option_action
                    break
            if chosen_action is None:
                print("  [WARN] Invalid selection. Enter 1, 2, 3, 4, or 5.")

        selected_actions[item.package_path] = chosen_action

        apply_raw = input("  Apply to all similar JPEGs in this document? [y/N]: ").strip().lower()
        if apply_raw in {"y", "yes"}:
            apply_to_similar[similarity_key] = chosen_action
        print("")

    return selected_actions


def cmd_scan(args: argparse.Namespace) -> int:
    policy = _optimization_policy_from_args(args)
    result = scan_document(args.target)
    print(
        render_scan_report(
            result,
            mode="hard",
            preset=args.preset,
            batch=True,
            analysis_label="SCAN ONLY / SMART OFFICE RULES",
            policy=policy,
        )
    )
    return 0 if not result.errors else 1


def cmd_ask(args: argparse.Namespace) -> int:
    policy = _optimization_policy_from_args(args)
    if args.mode == "safe":
        selected_actions = _prompt_safe_actions(args.target, args.preset, policy)
        result = write_safe_document(
            args.target,
            preset=args.preset,
            batch=False,
            selected_actions=selected_actions,
            output_dir=args.out,
            policy=policy,
        )
        print(render_process_report(result))
        return 0 if not result.errors else 1

    result = scan_document(args.target)
    print(render_scan_report(result, mode=args.mode, preset=args.preset, batch=False, policy=policy))
    print()
    print("[INFO] Alpha limitation: interactive write operations are not enabled yet.")
    print("[INFO] This run is report-first and recommendation-only.")
    return 0 if not result.errors else 1


def cmd_batch(args: argparse.Namespace) -> int:
    policy = _optimization_policy_from_args(args)
    if args.mode == "safe":
        result = write_safe_document(args.target, preset=args.preset, batch=True, output_dir=args.out, policy=policy)
        print(render_process_report(result))
        return 0 if not result.errors else 1

    if args.mode == "hard":
        result = write_hard_batch_document(args.target, preset=args.preset, output_dir=args.out, policy=policy)
        print(render_process_report(result))
        return 0 if not result.errors else 1

    result = scan_document(args.target)
    print(render_scan_report(result, mode=args.mode, preset=args.preset, batch=True, policy=policy))
    print()
    print("[INFO] Alpha limitation: batch write operations are not enabled yet.")
    print("[INFO] This run is report-first and recommendation-only.")
    return 0 if not result.errors else 1


def cmd_fit_size(args: argparse.Namespace) -> int:
    target_mb = max(1.0, float(args.target_mb))
    result, attempts = write_fit_size_document(
        args.target,
        target_size_mb=target_mb,
        output_dir=args.out,
    )
    print("=" * 72)
    print("AUDION OFFICE IMAGE OPTIMIZER - FIT SIZE")
    print("=" * 72)
    print(f"Target size   : {_format_bytes(int(target_mb * 1024 * 1024))}")
    print("Mode          : HARD JPG")
    print("")
    for index, attempt in enumerate(attempts, start=1):
        status = "OK" if attempt.met_target else "try next"
        print(f"[{index:02d}] {attempt.limit_label:<24} -> {_format_bytes(attempt.output_size_bytes):>9}  {status}")
    print("")
    print(
        render_process_report(
            result,
            analysis_label=f"FIT SIZE <= {target_mb:g} MB / HARD JPG",
        )
    )
    if result.errors:
        return 1
    if result.output_size_bytes and result.output_size_bytes > int(target_mb * 1024 * 1024):
        print("")
        print("[WARN] Target size was not reached. Lower limit used: 1280x720, JPEG 65.")
    return 0


def cmd_normalize_srgb(args: argparse.Namespace) -> int:
    result = write_profile_normalized_document(
        args.target,
        profile_mode="normalize-srgb",
        embed_profile=bool(args.embed_icc),
        output_dir=args.out,
    )
    print(render_process_report(result, analysis_label="NORMALIZE TO SRGB / PILLOW CMS / BATCH"))
    return 0 if not result.errors else 1


def cmd_normalize_cmyk(args: argparse.Namespace) -> int:
    result = write_profile_normalized_document(
        args.target,
        profile_mode="normalize-cmyk",
        embed_profile=bool(args.embed_icc),
        output_dir=args.out,
    )
    print(render_process_report(result, analysis_label="NORMALIZE TO CMYK / PILLOW CMS / BATCH"))
    return 0 if not result.errors else 1


def cmd_extract_media(args: argparse.Namespace) -> int:
    result = extract_media(args.target, output_root=args.out)
    print(render_media_extract_report(result))
    return 0 if not result.errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audion-office-image-optimizer",
        description="Portable alpha scanner for embedded Office images in DOCX/PPTX packages.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a DOCX/PPTX file and print a report")
    _add_common_mode_args(scan)
    scan.set_defaults(func=cmd_scan)

    ask = sub.add_parser("ask", help="Interactive alpha mode (currently report-only)")
    _add_common_mode_args(ask)
    ask.set_defaults(func=cmd_ask)

    batch = sub.add_parser("batch", help="Batch alpha mode (currently report-only)")
    _add_common_mode_args(batch)
    batch.set_defaults(func=cmd_batch)

    fit_size = sub.add_parser("fit-size", help="Fit output DOCX/PPTX under target size using HARD JPG passes")
    fit_size.add_argument("target", help="Path to a DOCX or PPTX file")
    fit_size.add_argument("--target-mb", type=float, default=20.0, help="Target output size in MB. Defaults to 20.")
    fit_size.add_argument("--out", default=None, help="Output folder. Defaults to project output folder.")
    fit_size.set_defaults(func=cmd_fit_size)

    normalize_srgb = sub.add_parser("normalize-srgb", help="Normalize all supported embedded images to sRGB")
    normalize_srgb.add_argument("target", help="Path to a DOCX or PPTX file")
    normalize_srgb.add_argument("--embed-icc", action="store_true", help="Embed the target ICC profile into saved image parts")
    normalize_srgb.add_argument("--out", default=None, help="Output folder. Defaults to project output folder.")
    normalize_srgb.set_defaults(func=cmd_normalize_srgb)

    normalize_cmyk = sub.add_parser("normalize-cmyk", help="Normalize all supported embedded images to CMYK")
    normalize_cmyk.add_argument("target", help="Path to a DOCX or PPTX file")
    normalize_cmyk.add_argument("--embed-icc", action="store_true", help="Embed the target ICC profile into saved image parts")
    normalize_cmyk.add_argument("--out", default=None, help="Output folder. Defaults to project output folder.")
    normalize_cmyk.set_defaults(func=cmd_normalize_cmyk)

    extract_media_parser = sub.add_parser("extract-media", help="Extract word/media or ppt/media files into output/<document name>")
    extract_media_parser.add_argument("target", help="Path to a DOCX or PPTX file")
    extract_media_parser.add_argument("--out", default=None, help="Output root folder. Defaults to project output folder.")
    extract_media_parser.set_defaults(func=cmd_extract_media)

    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
