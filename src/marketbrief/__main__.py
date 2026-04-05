"""CLI entry point: python -m marketbrief"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="marketbrief",
        description="AI-powered market intelligence framework",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen = subparsers.add_parser("generate", help="Generate a market briefing report")
    gen.add_argument("--config", default="config", help="Path to config directory")
    gen.add_argument(
        "--output",
        choices=["stdout", "html", "pdf", "json", "markdown"],
        default="stdout",
        help="Output format (default: stdout)",
    )
    gen.add_argument("--no-ai", action="store_true", help="Data-only mode (skip Claude analysis)")

    # fetch
    fetch = subparsers.add_parser("fetch", help="Fetch market data without generating report")
    fetch.add_argument("source", choices=["market", "news", "calendar", "crypto", "etf", "fred", "all"], help="Data source to fetch")
    fetch.add_argument("--format", choices=["json", "table"], default="json", help="Output format")

    # push
    push = subparsers.add_parser("push", help="Push a generated report to delivery channels")
    push.add_argument("--channel", choices=["telegram", "feishu", "stdout"], default="stdout", help="Delivery channel")
    push.add_argument("--report", help="Path to report file (default: latest)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        from marketbrief.core.pipeline import run_pipeline

        run_pipeline(
            config_dir=args.config,
            output_format=args.output,
            skip_ai=args.no_ai,
        )
    elif args.command == "fetch":
        from marketbrief.core.pipeline import run_fetch

        run_fetch(source=args.source, output_format=args.format)
    elif args.command == "push":
        from marketbrief.core.pipeline import run_push

        run_push(channel=args.channel, report_path=args.report)


if __name__ == "__main__":
    main()