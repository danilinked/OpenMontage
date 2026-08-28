"""Google Veo video generation via the direct Gemini API (no reseller markup).

Uses GOOGLE_API_KEY against generativelanguage.googleapis.com's long-running
predict operation, as opposed to `veo_video` (fal.ai) or `heygen_video`
(HeyGen gateway), which both resell Veo through third parties.
"""

from __future__ import annotations

import mimetypes
import os
import time
from base64 import b64encode
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


class VeoDirect(BaseTool):
    name = "veo_direct"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "google"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    install_instructions = (
        "Set GOOGLE_API_KEY to a Google AI Studio API key.\n"
        "  Get one at https://aistudio.google.com/apikey\n"
        "  Veo access must be enabled for the key's project/tier."
    )
    agent_skills = ["ai-video-gen"]
    fallback_tools = ["veo_video", "heygen_video", "kling_video"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "native_audio": True,
        "direct_provider": True,
    }
    best_for = [
        "Veo generation with no reseller markup",
        "using an existing Google AI Studio / Gemini API key",
    ]
    not_good_for = ["projects without a Veo-enabled Google API key"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "operation": {
                "type": "string",
                "enum": ["text_to_video", "image_to_video"],
                "default": "text_to_video",
            },
            "model": {
                "type": "string",
                "enum": ["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"],
                "default": "veo-3.1-generate-preview",
            },
            "aspect_ratio": {"type": "string", "enum": ["16:9", "9:16"], "default": "16:9"},
            "duration_seconds": {"type": "integer", "default": 8},
            "negative_prompt": {"type": "string"},
            "image_path": {"type": "string", "description": "Local reference image for image_to_video"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "operation"]
    side_effects = ["writes video file to output_path", "calls Google Gemini API"]
    user_visible_verification = ["Watch generated clip for visual quality and motion"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "veo-3.1-generate-preview")
        duration = int(inputs.get("duration_seconds", 8))
        per_second = 0.15 if "fast" in model else 0.40
        return per_second * duration

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 90.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="GOOGLE_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        model = inputs.get("model", "veo-3.1-generate-preview")
        operation = inputs.get("operation", "text_to_video")

        instance: dict[str, Any] = {"prompt": inputs["prompt"]}
        if operation == "image_to_video":
            image_path = inputs.get("image_path")
            if not image_path:
                return ToolResult(success=False, error="image_to_video requires image_path")
            path = Path(image_path)
            if not path.exists():
                return ToolResult(success=False, error=f"Image not found: {image_path}")
            mime_type, _ = mimetypes.guess_type(path.name)
            instance["image"] = {
                "bytesBase64Encoded": b64encode(path.read_bytes()).decode("ascii"),
                "mimeType": mime_type or "image/png",
            }

        parameters: dict[str, Any] = {
            "aspectRatio": inputs.get("aspect_ratio", "16:9"),
            "durationSeconds": inputs.get("duration_seconds", 8),
        }
        if inputs.get("negative_prompt"):
            parameters["negativePrompt"] = inputs["negative_prompt"]

        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

        try:
            submit_resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predictLongRunning",
                headers=headers,
                json={"instances": [instance], "parameters": parameters},
                timeout=30,
            )
            if not submit_resp.ok:
                return ToolResult(
                    success=False,
                    error=f"Veo direct submit failed ({submit_resp.status_code}): {submit_resp.text[:1000]}",
                )
            op_name = submit_resp.json().get("name")
            if not op_name:
                return ToolResult(success=False, error=f"No operation name in response: {submit_resp.text[:500]}")

            # Poll the long-running operation until done.
            deadline = time.time() + 600
            op_data: dict[str, Any] = {}
            while time.time() < deadline:
                time.sleep(8)
                poll_resp = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/{op_name}",
                    headers={"x-goog-api-key": api_key},
                    timeout=30,
                )
                if not poll_resp.ok:
                    return ToolResult(
                        success=False,
                        error=f"Veo direct poll failed ({poll_resp.status_code}): {poll_resp.text[:1000]}",
                    )
                op_data = poll_resp.json()
                if op_data.get("done"):
                    break
            else:
                return ToolResult(success=False, error="Veo direct generation timed out after 600s")

            if "error" in op_data:
                return ToolResult(success=False, error=f"Veo direct generation error: {op_data['error']}")

            samples = (
                op_data.get("response", {})
                .get("generateVideoResponse", {})
                .get("generatedSamples", [])
            )
            if not samples:
                return ToolResult(success=False, error=f"No generated samples in response: {op_data}")

            video_uri = samples[0].get("video", {}).get("uri")
            if not video_uri:
                return ToolResult(success=False, error=f"No video URI in sample: {samples[0]}")

            video_resp = requests.get(video_uri, headers={"x-goog-api-key": api_key}, timeout=120)
            if not video_resp.ok:
                return ToolResult(
                    success=False,
                    error=f"Veo direct video download failed ({video_resp.status_code}): {video_resp.text[:500]}",
                )

            output_path = Path(inputs.get("output_path", "veo_direct_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(video_resp.content)

        except Exception as e:
            return ToolResult(success=False, error=f"Veo direct generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "google",
                "model": model,
                "operation": operation,
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
