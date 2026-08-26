"""Seedance (ByteDance) video generation via fal.ai API.

Default variant is 2.5 standard: cinematic clips with native audio,
director-level camera control, lip-sync from quoted dialogue, native
30-second single-pass generation (no stitching), and reference-to-video
ceilings of 30 images + 10 videos + 10 audio clips.

model_variant="mini" instead routes to the older, much cheaper Seedance
2.0 Mini tier (bytedance/seedance-2.0/mini/*, ~$0.09/s at 720p vs 2.5's
~$0.47/s) — use it when you don't need 2.5's longer single-pass duration
or larger reference ceilings and just want a cheap clip. Mini's own
duration/reference limits aren't independently confirmed here (fal.ai's
docs don't spell them out beyond price) — if a call 400s, it's likely
hitting a mini-specific ceiling narrower than what 2.5 supports.

No confirmed "fast" endpoint for 2.5 (unlike 2.0) — "fast" is not a valid
model_variant value; use "mini" for the budget path instead.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class SeedanceVideo(BaseTool):
    name = "seedance_video"
    version = "0.4.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "seedance"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys"
    )
    agent_skills = ["seedance-2-0", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "reference_to_video": True,
        "multiple_reference_images": True,
        "reference_image": True,
        "native_audio": True,
        "cinematic_quality": True,
        "camera_direction": True,
        "lip_sync": True,
        "multi_shot": True,
        "aspect_ratio": True,
        "seed": True,
    }
    best_for = [
        "preferred premium video gen when FAL_KEY is available",
        "cinematic trailers, teasers, and high-fidelity clips with native synchronized audio",
        "native 30-second single-pass shots — no stitching seams",
        "director-level camera control and multi-shot editing in a single generation",
        "lip-sync from quoted dialogue in prompts",
        "reference-conditioned generation (up to 30 images + 10 video clips + 10 audio clips)",
        "consistent character identity across shots",
        "model_variant='mini': same family at ~1/5 the price when you don't need 2.5's longer duration or reference ceilings",
    ]
    not_good_for = ["offline generation"]
    fallback_tools = ["veo_video", "kling_video", "minimax_video"]
    # Premium model — beat out "experimental stability" baseline. The scoring
    # engine reads quality_score directly when present (see lib/scoring.py).
    quality_score = 0.95

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video", "reference_to_video"],
                "default": "text_to_video",
            },
            "model_variant": {
                "type": "string",
                "enum": ["standard", "mini"],
                "default": "standard",
                "description": (
                    "standard = Seedance 2.5 (highest quality, ~$0.47/s at 720p). "
                    "mini = older, cheaper Seedance 2.0 Mini tier (~$0.09/s at 720p) — "
                    "no native 30s single-pass or expanded reference ceilings."
                ),
            },
            "duration": {
                "type": "string",
                "enum": [
                    "auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
                ],
                "default": "5",
                "description": "Duration in seconds, up to 30 (native single-pass, no stitching). 'auto' lets the model decide.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
                "default": "16:9",
            },
            "resolution": {
                "type": "string",
                "enum": ["480p", "720p"],
                "default": "720p",
            },
            "generate_audio": {
                "type": "boolean",
                "default": True,
                "description": "Generate synchronized audio (speech, SFX, ambient)",
            },
            "image_url": {
                "type": "string",
                "description": "Start frame image URL for image_to_video (jpg, png, webp)",
            },
            "image_path": {
                "type": "string",
                "description": "Local start-frame path for image_to_video. Auto-uploaded to fal.ai storage.",
            },
            "end_image_url": {
                "type": "string",
                "description": "Optional end frame URL for image_to_video",
            },
            "reference_image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 30 reference image URLs for reference_to_video (identity / wardrobe / setting / style anchors).",
            },
            "reference_image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local reference image paths for reference_to_video. Auto-uploaded to fal.ai storage.",
            },
            "reference_video_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 10 reference video clip URLs for reference_to_video (motion / camera / pacing anchors).",
            },
            "reference_audio_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 10 reference audio clip URLs for reference_to_video (voice / music / ambience anchors).",
            },
            "seed": {
                "type": "integer",
                "description": "Optional seed for reproducibility",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model_variant", "operation", "duration", "seed"]
    side_effects = ["writes video file to output_path", "calls fal.ai API"]
    user_visible_verification = [
        "Watch generated clip for motion coherence, audio sync, and visual quality"
    ]

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # fal.ai pricing is per-second by resolution, and differs by
        # generation for this family:
        #   2.5 standard: ~$0.4730/s at 720p, ~$0.2205/s at 480p.
        #   2.0 mini:     ~$0.0928/s at 720p, ~$0.0433/s at 480p.
        duration = inputs.get("duration", "5")
        secs = 5 if duration == "auto" else int(duration)
        resolution = inputs.get("resolution", "720p")
        variant = inputs.get("model_variant", "standard")
        if variant == "mini":
            rate = 0.0433 if resolution == "480p" else 0.0928
        else:
            rate = 0.2205 if resolution == "480p" else 0.4730
        return round(rate * secs, 2)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        variant = inputs.get("model_variant", "standard")
        return 60.0 if variant == "mini" else 120.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="FAL_KEY not set. " + self.install_instructions,
            )

        import requests

        start = time.time()
        operation = inputs.get("operation", "text_to_video")
        variant = inputs.get("model_variant", "standard")
        operation_path = operation.replace("_", "-")

        if variant == "mini":
            model_path = f"bytedance/seedance-2.0/mini/{operation_path}"
        else:
            model_path = f"bytedance/seedance-2.5/{operation_path}"

        payload: dict[str, Any] = {"prompt": inputs["prompt"]}

        if inputs.get("duration"):
            payload["duration"] = inputs["duration"]
        if inputs.get("aspect_ratio"):
            payload["aspect_ratio"] = inputs["aspect_ratio"]
        if inputs.get("resolution"):
            payload["resolution"] = inputs["resolution"]
        if "generate_audio" in inputs:
            payload["generate_audio"] = inputs["generate_audio"]
        if inputs.get("seed") is not None:
            payload["seed"] = inputs["seed"]

        if operation == "image_to_video":
            if inputs.get("image_url"):
                payload["image_url"] = inputs["image_url"]
            elif inputs.get("image_path"):
                from tools.video._shared import upload_image_fal
                payload["image_url"] = upload_image_fal(inputs["image_path"])
            if inputs.get("end_image_url"):
                payload["end_image_url"] = inputs["end_image_url"]

        if operation == "reference_to_video":
            ref_image_urls = list(inputs.get("reference_image_urls") or [])
            for local_path in inputs.get("reference_image_paths") or []:
                from tools.video._shared import upload_image_fal
                ref_image_urls.append(upload_image_fal(local_path))
            # Reference-to-video ceilings differ by generation:
            #   2.5 standard: 30 images + 10 video + 10 audio (confirmed).
            #   2.0 mini: not independently confirmed — use 2.0's known
            #   ceiling (9/3/3) as the conservative assumption.
            img_cap, vid_cap, audio_cap = (9, 3, 3) if variant == "mini" else (30, 10, 10)
            model_label = "Seedance 2.0 Mini" if variant == "mini" else "Seedance 2.5"
            if len(ref_image_urls) > img_cap:
                return ToolResult(
                    success=False,
                    error=f"{model_label} reference_to_video accepts at most {img_cap} reference images; got {len(ref_image_urls)}",
                )
            ref_video_urls = list(inputs.get("reference_video_urls") or [])
            if len(ref_video_urls) > vid_cap:
                return ToolResult(
                    success=False,
                    error=f"{model_label} reference_to_video accepts at most {vid_cap} reference videos; got {len(ref_video_urls)}",
                )
            ref_audio_urls = list(inputs.get("reference_audio_urls") or [])
            if len(ref_audio_urls) > audio_cap:
                return ToolResult(
                    success=False,
                    error=f"{model_label} reference_to_video accepts at most {audio_cap} reference audio clips; got {len(ref_audio_urls)}",
                )
            if ref_image_urls:
                payload["reference_image_urls"] = ref_image_urls
            if ref_video_urls:
                payload["reference_video_urls"] = ref_video_urls
            if ref_audio_urls:
                payload["reference_audio_urls"] = ref_audio_urls

        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }

        try:
            submit_resp = requests.post(
                f"https://queue.fal.run/{model_path}",
                headers=headers,
                json=payload,
                timeout=30,
            )
            submit_resp.raise_for_status()
            queue_data = submit_resp.json()
            status_url = queue_data["status_url"]
            response_url = queue_data["response_url"]

            while True:
                time.sleep(5)
                status_resp = requests.get(status_url, headers=headers, timeout=15)
                status_resp.raise_for_status()
                status = status_resp.json().get("status", "UNKNOWN")
                if status == "COMPLETED":
                    break
                if status in ("FAILED", "CANCELLED"):
                    return ToolResult(
                        success=False,
                        error=f"Seedance ({variant}) video generation {status.lower()}",
                    )

            result_resp = requests.get(response_url, headers=headers, timeout=30)
            result_resp.raise_for_status()
            data = result_resp.json()

            video_url = data["video"]["url"]
            video_response = requests.get(video_url, timeout=120)
            video_response.raise_for_status()

            output_path = Path(inputs.get("output_path", "seedance_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(video_response.content)

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Seedance ({variant}) video generation failed: {e}",
            )

        from tools.video._shared import probe_output

        probed = probe_output(output_path)
        return ToolResult(
            success=True,
            data={
                "provider": "seedance",
                "model": model_path,
                "prompt": inputs["prompt"],
                "operation": operation,
                "variant": variant,
                "aspect_ratio": inputs.get("aspect_ratio", "16:9"),
                "resolution": inputs.get("resolution", "720p"),
                "generate_audio": inputs.get("generate_audio", True),
                "seed": data.get("seed"),
                "output": str(output_path),
                "output_path": str(output_path),
                "format": "mp4",
                **probed,
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model_path,
        )
