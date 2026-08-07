# -*- coding: utf-8 -*-
"""Everything that physically moves a file into _quarantine/ instead of
leaving it in the scanned tree -- extensions.py for a file whose extension
never matched --extensions (_quarantine/excluded/), bad_files.py for a
file the scan itself flagged bad (_quarantine/bad_files/). Both run only
when --quarantine is passed -- see cli.py -- since moving files out of
the tree is a destructive, hard-to-reverse action a scan shouldn't take
without the caller explicitly asking for it."""

from metchurial.quarantine.bad_files import quarantine_bad_files
from metchurial.quarantine.extensions import quarantine_non_matching

__all__ = ["quarantine_bad_files", "quarantine_non_matching"]
