import sys
import re

words = ["insane", "1v5", "clutch", "in", "valorant", "ranked", "shorts"]
for kw in ["engineering", "machine learning", "linear algebra"]:
    for w in words:
        if w in kw:
            print(f"Match: word '{w}' is inside keyword '{kw}'")
