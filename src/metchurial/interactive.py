# -*- coding: utf-8 -*-
"""Interactive wizard, entered when `metchurial` is run with zero
arguments: prompts for every CLI flag one at a time and assembles the
equivalent argv token list, which cli.main() hands straight to the same
argparse parser a normal command-line invocation goes through. This module
owns no validation logic of its own (choices, mutual exclusivity, int
coercion) -- it only prompts and assembles tokens, then lets
ap.parse_args() stay the single source of truth for what's actually valid,
so the wizard can never drift from what the flags themselves accept.

Every prompt accepts a blank answer as "use the shown default" and
re-prompts on anything else invalid, so walking through it hitting Enter
every time reproduces today's plain-argparse defaults exactly. Prompt
order mirrors README's CLI reference table.

EOFError (raised by input() against a closed/non-interactive stdin) is
deliberately left to propagate -- cli.main() decides how to report that,
not this module.
"""

from __future__ import annotations

import os
import shlex

from metchurial.models.options import (DEFAULT_EXTENSIONS, DEFAULT_IDENTITY_GRANULARITY,
                                       DEFAULT_MAX_CHUNK_ITERATIONS, DEFAULT_SENSITIVE_COLUMNS,
                                       IDENTITY_GRANULARITIES)


def _prompt_root(question: str) -> str:
    while True:
        answer = input("{}: ".format(question)).strip()
        if answer and os.path.isdir(answer):
            return answer
        print("  '{}' is not a directory -- try again.".format(answer))


def _prompt_yes_no(question: str, default: bool = False) -> bool:
    default_label = "Yes" if default else "No"
    while True:
        answer = input("{}\n  1. Yes  2. No  [default: {}]: ".format(
            question, default_label)).strip().lower()
        if not answer:
            return default
        if answer in ("1", "y", "yes"):
            return True
        if answer in ("2", "n", "no"):
            return False
        print("  Please answer 1/yes or 2/no.")


def _prompt_int(question: str, default: int) -> int:
    while True:
        answer = input("{} [default: {}]: ".format(question, default)).strip()
        if not answer:
            return default
        try:
            return int(answer)
        except ValueError:
            print("  Please enter a whole number.")


def _prompt_choice(question: str, choices: tuple[str, ...], default: str) -> str:
    menu = "  ".join("{}. {}".format(i + 1, c) for i, c in enumerate(choices))
    default_index = choices.index(default) + 1
    while True:
        answer = input("{}\n  {}  [default: {} ({})]: ".format(
            question, menu, default_index, default)).strip()
        if not answer:
            return default
        if answer in choices:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1]
        print("  Please enter one of: {} (or its number).".format(", ".join(choices)))


def _prompt_list(question: str, default: tuple[str, ...]) -> tuple[str, ...]:
    answer = input("{} (space-separated) [default: {}]: ".format(
        question, " ".join(default))).strip()
    return tuple(answer.split()) if answer else default


def run_wizard() -> list[str]:
    """Returns the argv token list an equivalent hand-typed invocation
    would have passed to cli.main()."""
    print("No arguments given -- entering interactive mode. Press Enter on "
         "any question to accept its default.\n")

    root = _prompt_root("Root directory to scan recursively")
    argv = [root]

    sensitive_columns = _prompt_list("Sensitive column names", DEFAULT_SENSITIVE_COLUMNS)
    if sensitive_columns != DEFAULT_SENSITIVE_COLUMNS:
        argv += ["--sensitive-columns", *sensitive_columns]

    extensions = _prompt_list("File extensions to scan (without the dot)", DEFAULT_EXTENSIONS)
    if extensions != DEFAULT_EXTENSIONS:
        argv += ["--extensions", *extensions]

    if _prompt_yes_no("Print verbose per-file ANTLR/quarantine detail to stderr?"):
        argv.append("--verbose")

    workers = _prompt_int("Worker processes to scan across", 1)
    if workers != 1:
        argv += ["--workers", str(workers)]

    max_chunk_iterations = _prompt_int(
        "Max resync-driver iterations per statement chunk", DEFAULT_MAX_CHUNK_ITERATIONS)
    if max_chunk_iterations != DEFAULT_MAX_CHUNK_ITERATIONS:
        argv += ["--max-chunk-iterations", str(max_chunk_iterations)]

    extract_metadata = _prompt_yes_no(
        "Extract metadata (table/column/function/relation refs + query identity)?")
    if extract_metadata:
        argv.append("--extract-metadata")

        granularity = _prompt_choice(
            "core_id granularity (loosest to strictest)",
            IDENTITY_GRANULARITIES, DEFAULT_IDENTITY_GRANULARITY)
        if granularity != DEFAULT_IDENTITY_GRANULARITY:
            argv += ["--identity-granularity", granularity]

        if _prompt_yes_no("Also compute pairwise query similarity (--query-similarity)?"):
            argv.append("--query-similarity")

    # A single 3-way menu, not two yes/no prompts: --split-selects and
    # --un-split-selects are mutually exclusive in cli.py, so the wizard
    # must never be able to construct both at once.
    split_mode = _prompt_choice(
        "Select-block split mode", ("none", "split", "un-split"), "none")
    if split_mode == "split":
        argv.append("--split-selects")
    elif split_mode == "un-split":
        argv.append("--un-split-selects")

    if _prompt_yes_no("Mask literal values in place for every finding (--mask-literals)?"):
        argv.append("--mask-literals")

    print("\nEquivalent command:\n  metchurial {}\n".format(
        " ".join(shlex.quote(a) for a in argv)))
    return argv
