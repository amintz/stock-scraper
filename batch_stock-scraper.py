#! /usr/bin/env python3

import subprocess

term_list = [
    "brazilian"
    "portuguese",
    "british",
    "canadian",
    "austrian",
    "nigerian",
    "belgian",
    "german",
    "philippine"
]

for term in term_list:
    subprocess.run(["./stock-scraper.py", term])
