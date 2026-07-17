# -*- coding: utf-8 -*-
"""Bundling entrypoint for stickytape -- kept separate from
src/cli.py so the package can still be `python -m`-run
normally in dev mode without going through this file.

Stickytape wraps this whole file (plus every inlined module) in a
`with <temporary-dir>:` block that deletes the extracted-modules directory
the instant this file finishes executing. That's fine for a normal run
(the directory only needs to survive for the `main()` call right below),
but it breaks --workers on the *spawn* start method (the only one
available on Windows, and the default on macOS): each worker process
re-executes this entire file during its own bootstrap, __name__ is
"__mp_main__" (not "__main__") there, so `main()` is skipped -- and
control falls straight out of the enclosing `with` block, deleting that
worker's own temp directory before it has run a single task. Any module
imported lazily during actual parsing (e.g. antlr4's LL1Analyzer) then
can't be found on disk anymore. Neutralizing shutil.rmtree here keeps
that worker's extracted modules on disk for the rest of its process
lifetime, which is fine -- a pool worker process is short-lived and the
OS reclaims its temp dir eventually regardless.
"""

if __name__ != "__main__":
    import shutil
    shutil.rmtree = lambda *args, **kwargs: None

from src.cli import main

if __name__ == "__main__":
    main()
