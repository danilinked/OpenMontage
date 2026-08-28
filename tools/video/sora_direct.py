"""OpenAI Sora video generation via the direct OpenAI API (no reseller markup).

Uses OPENAI_API_KEY against api.openai.com/v1/videos, as opposed to
`heygen_video` (HeyGen gateway), which resells Sora through a third party.
Access to the Sora API is limited/tiered on OpenAI's side — a 403/404 on
first use signals the key's account doesn't have Sora API access yet, not a
code bug.
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


class SoraDirect(BaseTool):
    name = "sora_direct"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "openai"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    install_instructions = (
        "Set OPENAI_API_KEY to an OpenAI API key with Sora API access enabled.\n"
        "  Get one at https://platform.openai.com/api-keys\n"
        "  Sora API access is separate/limited from general API access; check\n"
        "  your account's model access page if generation fails with 403/404."
    )
    agent_skills = ["ai-video-gen"]
    fallback_tools = ["heygen_video", "kling_video"]

    capabilities = ["text_to_video", "image_to_video"]
    supports = {
        "text_to_video": True,
        "image_to_video": True,
        "direct_provider": True,
    }
    best_for = [
        "Sora generation with no reseller markup",
        "using an existing OpenAI API key",
    ]
    not_good_for = ["accounts without Sora API access enabled"]

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
                "enum": ["sora-2", "sora-2-pro"],
                "default": "sora-2",
            },
            "seconds": {"type": "string", "enum": ["4", "8", "12"], "default": "8"},
            "size": {"type": "string", "default": "1280x720"},
            "image_path": {"type": "string", "description": "Local reference image for image_to_video"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=500, network_required=True)
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "seconds"]
    side_effects = ["writes video file to output_path", "calls OpenAI API"]
    user_visible_verification = ["Watch generated clip for visual quality and motion"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("OPENAI_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "sora-2")
        seconds = int(inputs.get("seconds", "8"))
        per_second = 0.50 if "pro" in model else 0.10
        return per_second * seconds

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 120.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(success=False, error="OPENAI_API_KEY not set. " + self.install_instructions)

        import requests

        start = time.time()
        model = inputs.get("model", "sora-2")
        operation = inputs.get("operation", "text_to_video")
        headers = {"Authorization": f"Bearer {api_key}"}

        data: dict[str, Any] = {
            "model": model,
            "prompt": inputs["prompt"],
            "seconds": inputs.get("seconds", "8"),
            "size": inputs.get("size", "1280x720"),
        }

        try:
            if operation == "image_to_video":
                image_path = inputs.get("image_path")
                if not image_path:
                    return ToolResult(success=False, error="image_to_video requires image_path")
                path = Path(image_path)
                if not path.exists():
                    return ToolResult(success=False, error=f"Image not found: {image_path}")
                with open(path, "rb") as f:
                    submit_resp = requests.post(
                        "https://api.openai.com/v1/videos",
                        headers=headers,
                        data=data,
                        files={"input_reference": (path.name, f, "image/png")},
                        timeout=60,
                    )
            else:
                submit_resp = requests.post(
                    "https://api.openai.com/v1/videos",
                    headers={**headers, "Content-Type": "application/json"},
                    json=data,
                    timeout=30,
                )

            if not submit_resp.ok:
                return ToolResult(
                    success=False,
                    error=f"Sora direct submit failed ({submit_resp.status_code}): {submit_resp.text[:1000]}",
                )
            video_id = submit_resp.json().get("id")
            if not video_id:
                return ToolResult(success=False, error=f"No video id in response: {submit_resp.text[:500]}")

            deadline = time.time() + 600
            status = "queued"
            while time.time() < deadline:
                time.sleep(8)
                status_resp = requests.get(
                    f"https://api.openai.com/v1/videos/{video_id}", headers=headers, timeout=30
                )
                if not status_resp.ok:
                    return ToolResult(
                        success=False,
                        error=f"Sora direct status check failed ({status_resp.status_code}): {status_resp.text[:1000]}",
                    )
                status_data = status_resp.json()
                status = status_data.get("status", "unknown")
                if status in ("completed", "failed"):
                    break
            else:
                return ToolResult(success=False, error="Sora direct generation timed out after 600s")

            if status == "failed":
                return ToolResult(success=False, error=f"Sora direct generation failed: {status_data}")

            content_resp = requests.get(
                f"https://api.openai.com/v1/videos/{video_id}/content", headers=headers, timeout=120
            )
            if not content_resp.ok:
                return ToolResult(
                    success=False,
                    error=f"Sora direct content download failed ({content_resp.status_code}): {content_resp.text[:500]}",
                )

            output_path = Path(inputs.get("output_path", "sora_direct_output.mp4"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(content_resp.content)

        except Exception as e:
            return ToolResult(success=False, error=f"Sora direct generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "openai",
                "model": model,
                "operation": operation,
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
