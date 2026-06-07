"""Webhook notification helpers."""

from __future__ import annotations

import json
from typing import Iterable

from .models import AvailabilityResult


def format_summary(results: Iterable[AvailabilityResult]) -> str:
    """Build a compact human-readable status summary."""

    lines = []
    for result in results:
        location = result.availability_domain
        if result.fault_domain:
            location = f"{location}/{result.fault_domain}"
        count = "unknown" if result.available_count is None else str(result.available_count)
        lines.append(
            f"{location}: {result.status} ({result.shape}, {result.ocpus:g} OCPU, "
            f"{result.memory_gb:g} GB, available count: {count})"
        )
    return "\n".join(lines)


def send_webhook(webhook_url: str, results: list[AvailabilityResult]) -> None:
    """Send the capacity summary to a generic Discord/Slack-compatible webhook."""

    import requests

    available = any(result.is_available for result in results)
    title = "OCI Ampere A1 capacity is AVAILABLE" if available else "OCI Ampere A1 capacity is unavailable"
    payload = {
        "content": f"{title}\n```\n{format_summary(results)}\n```",
        "text": f"{title}\n{format_summary(results)}",
    }
    response = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=20)
    response.raise_for_status()
