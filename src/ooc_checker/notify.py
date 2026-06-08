"""Webhook notification helpers."""

from __future__ import annotations

import json
import logging
from typing import Iterable

from .models import AvailabilityResult

logger = logging.getLogger(__name__)


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
    """Send the capacity summary to a generic Discord/Slack-compatible webhook.

    Catches request errors so a webhook failure never crashes the checker.
    """

    import requests

    available = any(result.is_available for result in results)
    title = "OCI Ampere A1 capacity is AVAILABLE" if available else "OCI Ampere A1 capacity is unavailable"
    payload = {
        "content": f"{title}\n```\n{format_summary(results)}\n```",
        "text": f"{title}\n{format_summary(results)}",
    }
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Webhook delivery failed: %s", exc)


def send_telegram(token: str, chat_id: str, results: list[AvailabilityResult]) -> None:
    """Send the capacity summary to a Telegram chat using a Bot token.

    Catches request errors so a Telegram failure never crashes the checker.
    """

    import requests

    available = any(result.is_available for result in results)
    title = "OCI Ampere A1 capacity is AVAILABLE" if available else "OCI Ampere A1 capacity is unavailable"
    message = f"*{title}*\n\n```\n{format_summary(results)}\n```"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Telegram notification failed: %s", exc)

