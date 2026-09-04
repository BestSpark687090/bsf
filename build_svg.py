#!/usr/bin/env python3
# AI Generated.
# Rebuilds single.svg from single.html + single-classic.min.js.
#
# Before running this, regenerate single-classic.min.js if single-classic.js changed:
#   npx esbuild single-classic.js --minify --outfile=single-classic.min.js
#
# single-classic.js itself is a hand-maintained classic-script (non-module) fork of
# single.js - if you change single.js (or index.js) you need to re-apply the same
# changes there (async IIFE instead of top-level await/static import, createElementNS
# for elements created against the outer XML document in makeCard(), etc.) since SVG
# documents don't support <script type="module"> in Chromium (crbug.com/717643).
import re
import os

base = os.path.dirname(os.path.abspath(__file__)) + "/"

with open(base + "single.html", encoding="utf-8") as f:
    html = f.read()
with open(base + "single-classic.min.js", encoding="utf-8") as f:
    js = f.read()

# 1. strip comments
html = re.sub(r'<!--.*?-->', '', html, flags=re.S)

# 2. strip meta tags
html = re.sub(r'<meta\b[^>]*/?>\s*', '', html, flags=re.S)

# 3. fix bare attrs we know about (bare boolean attrs, possibly surrounded by whitespace/newlines)
html = re.sub(r'(?<=[\s])async(?=[\s/>])(?!=)', 'async="async"', html)
html = re.sub(r'(?<=[\s])allowfullscreen(?=[\s/>])(?!=)', 'allowfullscreen="allowfullscreen"', html)
html = re.sub(r'(?<=[\s])defer(?=[\s/>])(?!=)', 'defer="defer"', html)

# 4. escape srcdoc attribute value
html = html.replace('srcdoc="<h1>Loading...</h1>"', 'srcdoc="&lt;h1&gt;Loading...&lt;/h1&gt;"')

# 4a. SVG-build-only limitation notice: #game-modal is position:fixed, which pins to
# the real browser viewport - fine in a normal tab, but position:fixed (and every
# workaround tried for it) is unreliable inside <foreignObject> across browsers, a
# known, long-standing rendering quirk. Rather than keep fighting that, force the page
# back to the top whenever a game opens (so the modal, wherever its reference frame
# actually is, at least lines up with visible content) and tell the user why, once,
# instead of silently producing a modal that's misaligned with no explanation.
html = html.replace(
    '</body>',
    '''<script>
(function(){
  var modal = document.getElementById("game-modal");
  if (!modal) return;
  var warned = false;
  var mo = new MutationObserver(function(){
    if (!modal.classList.contains("open")) return;
    document.getElementById("fo").scrollTo(0, 0);
    if (!warned) {
      warned = true;
      alert("games open at the top of the page. sorry! i can't really fix that...");
    }
  });   
  mo.observe(modal, { attributes: true, attributeFilter: ["class"] });
})();
</script>
</body>''',
    1,
)

# 4b. self-close void elements - valid bare (eg. "<br>") in HTML, invalid in XML.
# Only touches tags not already self-closed, and only these specific void tags -
# leaves everything else (script/style/div/etc.) alone since closing those the same
# way would corrupt real content.
VOID_TAGS = "br|img|input|hr|link|area|col|embed|source|track|wbr|base"
def close_void(m):
    tag = m.group(0)
    return tag[:-1].rstrip() + " />"
html = re.sub(r'<(?:' + VOID_TAGS + r')\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*(?<!/)>', close_void, html, flags=re.I)

# 5. CDATA-wrap style/script bodies BEFORE inlining main js
def wrap_style(m):
    return '<style' + m.group(1) + '>/*<![CDATA[*/' + m.group(2) + '/*]]>*/</style>'
html = re.sub(r'<style([^>]*)>(.*?)</style>', wrap_style, html, flags=re.S)

def wrap_script(m):
    attrs, body = m.group(1), m.group(2)
    if body.strip() == '':
        return m.group(0)
    return '<script' + attrs + '>//<![CDATA[\n' + body + '\n//]]></script>'
html = re.sub(r'<script((?:(?!src=)[^>])*)>(.*?)</script>', wrap_script, html, flags=re.S)

# 6. remove the external single.js script tag - not relying on defer inside foreignObject,
# the main script gets inserted right before </body> instead (step below), where all
# elements it touches (eg. modal-close) already exist.
html = re.sub(r'\s*<script[^>]*src="single\.js"[^>]*></script>\n?', '\n', html)

assert html.count('</body>') == 1, html.count('</body>')

main_script = '<script>//<![CDATA[\n' + js + '\n//]]></script>\n'
html = html.replace('</body>', main_script + '</body>')

# 7. strip doctype, add xmlns
html = re.sub(r'<!doctype html>\s*', '', html, flags=re.I)
html = html.replace('<html lang="en">', '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">')

svg = '''<svg xmlns="http://www.w3.org/2000/svg" style="display:block;overflow:hidden;background:#000">
<foreignObject id="fo" x="0" y="0" width="100%" height="100%" style="overflow-y:scroll">
''' + html + '''
</foreignObject>
<script>//<![CDATA[
var fo = document.getElementById("fo");
function r(){fo.setAttribute("width", window.innerWidth); fo.setAttribute("height", window.innerHeight);}
r();
window.addEventListener("resize", r);
//]]></script>
</svg>
'''

with open(base + "single.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("wrote", len(svg), "bytes to", base + "single.svg")
