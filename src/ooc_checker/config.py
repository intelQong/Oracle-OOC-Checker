"""Configuration parsing for the Oracle out-of-capacity checker."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping

DEFAULT_SHAPE = "VM.Standard.A1.Flex"
DEFAULT_OCPUS = 1.0
DEFAULT_MEMORY_GB = 6.0


@dataclass(frozen=True)
class CheckerConfig:
    """Runtime settings for a capacity report check."""

    compartment_id: str
    availability_domains: tuple[str, ...]
    shape: str = DEFAULT_SHAPE
    ocpus: float = DEFAULT_OCPUS
    memory_gb: float = DEFAULT_MEMORY_GB
    fault_domain: str | None = None
    oci_config_file: str | None = None
    oci_profile: str = "DEFAULT"
    auth: str = "config"
    webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    notify_on_unavailable: bool = False
    exit_nonzero_when_unavailable: bool = False
    output_json: bool = False


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _env_bool(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    value = env.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_from_env(env: Mapping[str, str] | None = None) -> CheckerConfig:
    """Create checker configuration from environment variables."""

    source = os.environ if env is None else env
    compartment_id = source.get("OCI_COMPARTMENT_ID") or source.get("OCI_TENANCY")
    if not compartment_id:
        raise ValueError("Set OCI_COMPARTMENT_ID to the root tenancy OCID or target compartment OCID.")

    availability_domains = _split_csv(source.get("OCI_AVAILABILITY_DOMAINS"))
    if not availability_domains:
        raise ValueError(
            "Set OCI_AVAILABILITY_DOMAINS to one or more AD names, for example 'abcd:US-ASHBURN-AD-1'."
        )

    config_file = source.get("OCI_CONFIG_FILE")
    if config_file:
        config_file = str(Path(config_file).expanduser())

    return CheckerConfig(
        compartment_id=compartment_id,
        availability_domains=availability_domains,
        shape=source.get("OCI_SHAPE", DEFAULT_SHAPE),
        ocpus=float(source.get("OCI_OCPUS", DEFAULT_OCPUS)),
        memory_gb=float(source.get("OCI_MEMORY_GB", DEFAULT_MEMORY_GB)),
        fault_domain=source.get("OCI_FAULT_DOMAIN") or None,
        oci_config_file=config_file,
        oci_profile=source.get("OCI_PROFILE", "DEFAULT"),
        auth=source.get("OCI_AUTH", "config").strip().lower(),
        webhook_url=source.get("WEBHOOK_URL") or None,
        telegram_bot_token=source.get("TELEGRAM_BOT_TOKEN") or None,
        telegram_chat_id=source.get("TELEGRAM_CHAT_ID") or None,
        notify_on_unavailable=_env_bool(source, "NOTIFY_ON_UNAVAILABLE"),
        exit_nonzero_when_unavailable=_env_bool(source, "EXIT_NONZERO_WHEN_UNAVAILABLE"),
        output_json=_env_bool(source, "OUTPUT_JSON"),
    )

