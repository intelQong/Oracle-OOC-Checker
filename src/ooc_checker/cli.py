"""Command line entrypoint for the OCI Ampere A1 capacity checker."""

from __future__ import annotations

import argparse
import json
import sys
import time

from .checker import check_capacity
from .config import load_from_env
from .notify import format_summary, send_webhook


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Oracle Cloud Ampere A1 Flex capacity with Compute Capacity Reports.")
    parser.add_argument("--watch", action="store_true", help="Run forever instead of checking once.")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between checks in --watch mode. Default: 300.")
    return parser.parse_args(argv)


def execute_check() -> tuple[int, bool]:
    config = load_from_env()
    results = check_capacity(config)
    is_available = any(result.is_available for result in results)

    if config.output_json:
        print(json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True))
    else:
        print(format_summary(results))

    should_notify = bool(config.webhook_url) and (is_available or config.notify_on_unavailable)
    if should_notify:
        send_webhook(config.webhook_url or "", results)

    if not is_available and config.exit_nonzero_when_unavailable:
        return 2, is_available
    return 0, is_available


def run_once() -> int:
    exit_code, _ = execute_check()
    return exit_code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.watch:
        return run_once()

    while True:
        exit_code, is_available = execute_check()
        if is_available:
            return exit_code
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
