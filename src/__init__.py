# -*- coding: utf-8 -*-
"""Puts generated/ on sys.path as a flat directory (not a sub-package), so
every module here can import the generated lexer/parser directly, e.g.
`from Db2Lexer import Db2Lexer`. Required because the generated code itself
uses flat, absolute imports, matching grammars-v4's generated-code layout.
"""

import os
import sys

_GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated")
if _GENERATED_DIR not in sys.path:
    sys.path.insert(0, _GENERATED_DIR)
