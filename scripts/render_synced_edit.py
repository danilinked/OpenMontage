"""Render an edit_decisions.json (typically edit_decisions.synced.json, produced
by the OpenCut sync-back script) through OpenMontage's real VideoCompose tool —
routes to Remotion or HyperFrames per edit_decisions.render_runtime.

Usage:
    .venv/bin/python scripts/render_synced_edit.py <edit_decisions.json> <output.mp4> [--runtime remotion|hyperframes]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.video.video_compose import VideoCompose  # noqa: E402


def mirror_cuts_into_public(edit_decisions: dict, slug: str) -> None:
    """Copy each cut's source video into remotion-composer/public/<slug>/,
    and set cut.source to a path RELATIVE to remotion-composer/public/
    (e.g. "camping-comodo-guia/video/hero.mp4"), NOT an absolute path.

    This matters: video_compose.py's _remotion_render only converts
    cut.source to a file:// URI when Path(source).resolve() already exists
    as a real file relative to this script's cwd. A relative public/-style
    path won't resolve from here, so that conversion no-ops and the plain
    relative string reaches Explainer.tsx's resolveAsset(), which routes
    anything that isn't absolute/http/data through Remotion's own
    staticFile() helper — the actually-supported way to serve local video
    to the renderer. An absolute file:// URI, by contrast, 404s inside
    Remotion's webpack-bundle temp dir (its own proxy only serves files
    that were present under public/ at bundle time via staticFile(),
    not arbitrary filesystem paths handed to OffthreadVideo at render time).

    remotion-composer/public/* is gitignored, so this mirror doesn't
    survive a repo restore — regenerate it from the real source assets
    under projects/<slug>/assets/ before every render.
    """
    public_dir = ROOT_DIR / "remotion-composer" / "public" / slug
    for cut in edit_decisions.get("cuts", []):
        source = Path(cut["source"])
        if not source.is_absolute():
            source = (ROOT_DIR / source).resolve()
        if not source.exists():
            print(f"  warning: source missing, skipping mirror: {source}")
            continue
        subdir = "video" if source.suffix.lower() in (".mp4", ".mov", ".webm") else "images"
        dest = public_dir / subdir / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
            shutil.copyfile(source, dest)
        cut["source"] = f"{slug}/{subdir}/{source.name}"


def mirror_narration_into_public(edit_decisions: dict, slug: str) -> None:
    """Same reasoning as mirror_cuts_into_public, but for audio.narration.src
    — it's a separate field, not part of cuts[], so needs its own pass."""
    narration = edit_decisions.get("audio", {}).get("narration")
    if not narration or not narration.get("src"):
        return
    public_dir = ROOT_DIR / "remotion-composer" / "public" / slug
    source = Path(narration["src"])
    if not source.is_absolute():
        source = (ROOT_DIR / source).resolve()
    if not source.exists():
        print(f"  warning: narration source missing, skipping mirror: {source}")
        return
    dest = public_dir / "audio" / source.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
        shutil.copyfile(source, dest)
    narration["src"] = f"{slug}/audio/{source.name}"


def build_hyperframes_audio_manifest(edit_decisions: dict) -> dict:
    """HyperFramesCompose._resolve_audio_refs expects
    audio.narration.segments[].asset_id resolved against asset_manifest —
    NOT the flat {src, volume} shape edit_decisions.json actually has here.
    Without this, _resolve_audio_refs silently iterates an empty list and
    the render comes out with zero audio tracks (no error — just missing
    sound). Rewrite narration into one full-length segment and return the
    matching asset_manifest entry.
    """
    narration = edit_decisions.get("audio", {}).get("narration")
    if not narration or not narration.get("src"):
        return {"assets": []}
    source = Path(narration["src"])
    if not source.is_absolute():
        source = (ROOT_DIR / source).resolve()
    asset_id = "narration_main"
    edit_decisions["audio"]["narration"] = {
        "segments": [{"asset_id": asset_id, "start_seconds": 0}],
    }
    return {"assets": [{"id": asset_id, "path": str(source)}]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("edit_decisions_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--slug", required=True, help="Project slug, for the remotion-composer/public/<slug> asset mirror")
    parser.add_argument("--runtime", choices=["remotion", "hyperframes"], default=None)
    args = parser.parse_args()
    # HyperFrames runs its render CLI with cwd=workspace_path, so a relative
    # output_path silently lands inside the workspace instead of where the
    # caller meant — always pass an absolute path.
    args.output_path = args.output_path.resolve()

    edit_decisions = json.loads(args.edit_decisions_path.read_text())
    if args.runtime:
        edit_decisions["render_runtime"] = args.runtime

    runtime = edit_decisions.get("render_runtime")
    print(f"render_runtime = {runtime!r}")
    if runtime == "remotion":
        # HyperFramesCompose copies assets into its own workspace_path/assets/
        # itself (see tools/video/hyperframes_compose.py) — this public/
        # mirroring dance is a Remotion-specific workaround, not needed there.
        print("mirroring cut assets into remotion-composer/public/...")
        mirror_cuts_into_public(edit_decisions, args.slug)
        mirror_narration_into_public(edit_decisions, args.slug)
        # cuts[].source is already a real path, not an asset-manifest ID —
        # an empty manifest is fine on the Remotion path, the id -> path
        # lookup in video_compose.py just no-ops.
        asset_manifest = {"assets": []}
    elif runtime == "hyperframes":
        print("building narration asset_manifest for hyperframes...")
        asset_manifest = build_hyperframes_audio_manifest(edit_decisions)
    else:
        asset_manifest = {"assets": []}

    tool = VideoCompose()
    result = tool.execute(
        {
            "operation": "render",
            "edit_decisions": edit_decisions,
            "asset_manifest": asset_manifest,
            "output_path": str(args.output_path),
        }
    )

    if not result.success:
        print(f"FAILED: {result.error}", file=sys.stderr)
        return 1

    print(f"OK: wrote {args.output_path}")
    if result.data:
        print(json.dumps(result.data, indent=2, default=str)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
