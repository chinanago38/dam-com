#!/usr/bin/env python3
"""tools/bodies/*.html のうち本文3000字以上のものを detailed.txt に追加して再生成する。"""
import os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
det_p = os.path.join(ROOT, "tools", "detailed.txt")
det = {l.strip() for l in open(det_p, encoding="utf-8") if l.strip() and not l.startswith("#")}
added, short = [], []
for f in sorted(os.listdir(os.path.join(ROOT, "tools", "bodies"))):
    slug = f[:-5]
    t = open(os.path.join(ROOT, "tools", "bodies", f), encoding="utf-8").read().split("\n", 2)
    if len(t) < 3:
        continue
    n = len(re.sub(r"\s", "", re.sub(r"<[^>]+>", "", t[2])))
    if n >= 3000 and slug not in det:
        added.append((slug, n))
    elif n < 3000:
        short.append((slug, n))
with open(det_p, "a", encoding="utf-8") as fp:
    for s, _ in added:
        fp.write(s + "\n")
subprocess.run(["python3", os.path.join(ROOT, "tools", "build.py")], check=True)
print("added:", added); print("short:", short)
