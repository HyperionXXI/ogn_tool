"""Thin run-history CLI consumer for reporting APIs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from ogn_tool.reporting import (
    compare_run_bundles,
    compute_network_evolution,
    get_latest_run,
)

from .cli_formatters import (
    format_latest_run,
    format_network_evolution,
    format_run_comparison,
)



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ogn-runs', description='OGN run history commands')
    subparsers = parser.add_subparsers(dest='command', required=True)

    latest_parser = subparsers.add_parser('latest', help='Show latest analysis run')
    latest_parser.add_argument('registry', help='Path to the run registry directory')

    compare_parser = subparsers.add_parser('compare', help='Compare two analysis run bundles')
    compare_parser.add_argument('run_a', help='Path to the older or left bundle')
    compare_parser.add_argument('run_b', help='Path to the newer or right bundle')

    evolution_parser = subparsers.add_parser('evolution', help='Show network evolution from the registry')
    evolution_parser.add_argument('registry', help='Path to the run registry directory')
    evolution_parser.add_argument('--last', type=int, default=10, help='Number of latest runs to inspect')

    return parser



def main(argv: Sequence[str] | None = None) -> int:
    """Run the thin CLI for run-history reporting commands."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == 'latest':
        print(format_latest_run(get_latest_run(Path(args.registry))))
        return 0

    if args.command == 'compare':
        print(format_run_comparison(compare_run_bundles(Path(args.run_a), Path(args.run_b))))
        return 0

    if args.command == 'evolution':
        print(format_network_evolution(compute_network_evolution(Path(args.registry), last_n=args.last)))
        return 0

    parser.error('Unknown command')
    return 2


__all__ = ['main']
