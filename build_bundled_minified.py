#!/usr/bin/env python3
# Rebuilds single-bundled-minified.html from single.html + single.js:
#   1. minify single.js -> single.min.js (esbuild)
#   2. inline single.min.js into single.html in place of the external <script> tag
#   3. run the whole document through html-minifier-terser (collapses whitespace,
#      strips comments, minifies any remaining inline CSS/JS)
#
# Needs `npx esbuild` and `npx html-minifier-terser` on PATH (both installed on
# first use via npx if missing).
import re
import os
import subprocess

base = os.path.dirname(os.path.abspath(__file__)) + "/"

single_js = base + "single.js"
single_min_js = base + "single.min.js"
single_html = base + "single.html"
out_path = base + "single-bundled-minified.html"

print("minifying single.js...")
subprocess.run(
    ["npx", "esbuild", single_js, "--minify", "--format=esm", f"--outfile={single_min_js}"],
    check=True,
)

with open(single_html, encoding="utf-8") as f:
    html = f.read()
with open(single_min_js, encoding="utf-8") as f:
    js = f.read().rstrip("\n")

# Replace the external script tag with the minified JS inlined in place, keeping the
# same attributes (defer, type=module) so behavior doesn't change.
new_html, n = re.subn(
    r'<script defer src="single\.js" type="module"></script>',
    lambda m: '<script defer type="module">' + js + '</script>',
    html,
)
assert n == 1, f"expected exactly one single.js script tag, found {n}"

tmp_path = base + "_bundled_tmp.html"
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(new_html)

print("running html-minifier-terser...")
subprocess.run(
    [
        "npx",
        "html-minifier-terser",
        "--collapse-whitespace",
        "--remove-comments",
        "--minify-css",
        "true",
        "--minify-js",
        "true",
        "-o",
        out_path,
        tmp_path,
    ],
    check=True,
)

os.remove(tmp_path)

print("wrote", os.path.getsize(out_path), "bytes to", out_path)
