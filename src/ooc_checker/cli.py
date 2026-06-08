"""Command line entrypoint for the OCI Ampere A1 capacity checker."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from .config import load_from_env
from .notify import format_summary, send_webhook
from .setup_wizard import SetupConfig, discover_from_oci, write_env_file

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Oracle Cloud Ampere A1 Flex capacity with Compute Capacity Reports.")
    parser.set_defaults(watch=False, interval=300)
    subparsers = parser.add_subparsers(dest="command")

    configure = subparsers.add_parser("configure", help="Generate a ready-to-edit .env configuration file.")
    configure.add_argument("--output", default=".env", help="Path to write. Default: .env.")
    configure.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    configure.add_argument("--compartment-id", help="Tenancy or compartment OCID. Defaults to tenancy from OCI config.")
    configure.add_argument("--availability-domains", help="Comma-separated AD names. Defaults to values discovered from OCI.")
    configure.add_argument("--shape", default="VM.Standard.A1.Flex", help="Shape to check. Default: VM.Standard.A1.Flex.")
    configure.add_argument("--ocpus", type=float, default=1.0, help="OCPUs to check. Default: 1.")
    configure.add_argument("--memory-gb", type=float, default=6.0, help="Memory in GB to check. Default: 6.")
    configure.add_argument("--auth", choices=("config", "instance_principal"), default="config", help="OCI auth method.")
    configure.add_argument("--config-file", default="~/.oci/config", help="OCI config path for API-key auth.")
    configure.add_argument("--profile", default="DEFAULT", help="OCI config profile. Default: DEFAULT.")
    configure.add_argument("--webhook-url", help="Optional Discord/Slack-compatible webhook URL.")
    configure.add_argument("--notify-on-unavailable", action="store_true", help="Send webhook messages even when capacity is unavailable.")
    configure.add_argument("--output-json", action="store_true", help="Set OUTPUT_JSON=true in the generated file.")
    configure.add_argument("--exit-nonzero-when-unavailable", action="store_true", help="Set EXIT_NONZERO_WHEN_UNAVAILABLE=true.")

    parser.add_argument("--watch", action="store_true", help="Run forever instead of checking once.")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between checks in --watch mode. Default: 300.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose/debug logging output.")
    return parser.parse_args(argv)


def execute_check() -> tuple[int, bool]:
    from .checker import check_capacity

    config = load_from_env()
    results = check_capacity(config)
    is_available = any(result.is_available for result in results)

    if config.output_json:
        print(json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True))
    else:
        print(format_summary(results))

    should_notify = is_available or config.notify_on_unavailable
    if should_notify:
        if config.webhook_url:
            send_webhook(config.webhook_url, results)
        if config.telegram_bot_token and config.telegram_chat_id:
            from .notify import send_telegram
            send_telegram(config.telegram_bot_token, config.telegram_chat_id, results)

    if not is_available and config.exit_nonzero_when_unavailable:
        return 2, is_available
    return 0, is_available


def run_once() -> int:
    exit_code, _ = execute_check()
    return exit_code


def _split_domains(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _post_configure_hint(destination: Path) -> str:
    """Return a platform-aware hint for loading the generated .env file."""

    if sys.platform == "win32":
        return (
            f"Wrote {destination}.\n"
            f"On PowerShell, load it with:\n"
            f"  Get-Content {destination} | ForEach-Object {{ if ($_ -and $_[0] -ne '#') {{ $k,$v = $_ -split '=',2; [Environment]::SetEnvironmentVariable($k,$v,'Process') }} }}\n"
            f"  ooc-checker\n"
            f"Or on Bash/WSL:\n"
            f"  set -a && . {destination} && set +a && ooc-checker"
        )
    return f"Wrote {destination}. Run: set -a && . {destination} && set +a && ooc-checker"


def configure(args: argparse.Namespace) -> int:
    compartment_id = args.compartment_id
    availability_domains = _split_domains(args.availability_domains)

    if args.auth == "config" and (not compartment_id or not availability_domains):
        discovered_compartment_id, discovered_domains = discover_from_oci(args.config_file, args.profile)
        compartment_id = compartment_id or discovered_compartment_id
        availability_domains = availability_domains or discovered_domains

    if not compartment_id:
        raise ValueError("Provide --compartment-id, or use --auth config with a valid OCI config file for discovery.")
    if not availability_domains:
        raise ValueError("Provide --availability-domains, or use --auth config with a valid OCI config file for discovery.")

    setup_config = SetupConfig(
        compartment_id=compartment_id,
        availability_domains=availability_domains,
        shape=args.shape,
        ocpus=args.ocpus,
        memory_gb=args.memory_gb,
        auth=args.auth,
        config_file=args.config_file,
        profile=args.profile,
        webhook_url=args.webhook_url,
        notify_on_unavailable=args.notify_on_unavailable,
        output_json=args.output_json,
        exit_nonzero_when_unavailable=args.exit_nonzero_when_unavailable,
    )
    destination = write_env_file(Path(args.output), setup_config, overwrite=args.force)
    print(_post_configure_hint(destination))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.WARNING,
    )

    if args.command == "configure":
        return configure(args)

    if not args.watch:
        return run_once()

    try:
        while True:
            try:
                exit_code, is_available = execute_check()
            except Exception:
                logger.exception("Check failed, retrying in %d seconds", args.interval)
                time.sleep(args.interval)
                continue
            if is_available:
                return exit_code
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
