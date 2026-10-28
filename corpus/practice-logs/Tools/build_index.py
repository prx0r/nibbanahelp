"""Embed logs.json into index.html by replacing the `const DATA = [...];` block.

Deterministic + safe: locates `const DATA =`, then finds the array bounds by
bracket-depth scanning that ignores brackets inside JSON strings, and swaps in
the pretty-printed contents of logs.json. Run after updating logs.json.

Usage:  python3 Tools/build_index.py logs.json index.html
"""
import json, sys, re

def find_array_span(text, start_idx):
    """Return (open_idx, close_idx_inclusive) of the JS array starting at/after start_idx."""
    i = text.index('[', start_idx)
    depth, in_str, esc = 0, False, False
    for j in range(i, len(text)):
        ch = text[j]
        if in_str:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return i, j
    raise ValueError("Unterminated DATA array")

def main(json_path, html_path):
    records = json.load(open(json_path, encoding='utf-8'))
    html = open(html_path, encoding='utf-8').read()
    m = re.search(r'const\s+DATA\s*=\s*', html)
    if not m:
        raise SystemExit("Could not find `const DATA =` in index.html")
    open_i, close_i = find_array_span(html, m.end())
    new_arr = json.dumps(records, ensure_ascii=False, indent=0)
    new_html = html[:open_i] + new_arr + html[close_i+1:]
    open(html_path, 'w', encoding='utf-8').write(new_html)
    print(f"Embedded {len(records)} records into {html_path}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
