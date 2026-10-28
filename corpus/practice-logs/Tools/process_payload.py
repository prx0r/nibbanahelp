"""Convert a browser-captured DhO payload (JSON) into a .txt matching the scraper output.

process_content() is the original scraper's function with ONE change: nested quotes
are processed deepest-first so double/nested quotes are preserved as nested
<quote>...<quote>...</quote>...</quote> markers. For single (non-nested) quotes and
quote-free text, output is byte-identical to the original scraper."""
import json, os, sys, html, re
from bs4 import BeautifulSoup

def _quote_depth(q):
    return len(q.find_parents('div', class_='quote'))

def process_content(content):
    content_copy = BeautifulSoup(str(content), 'html.parser')

    # Handle quotes. Process DEEPEST first so a nested quote is already converted
    # to its <quote>...</quote> marker before its parent quote is flattened,
    # preserving true nesting. (Original processed in document order, flattening.)
    quotes = content_copy.find_all('div', class_='quote')
    quotes.sort(key=_quote_depth, reverse=True)
    for quote in quotes:
        quote_content = quote.find('div', class_='quote-content')
        if quote_content:
            quote_text = quote_content.text.strip()
            quote.string = '\n\n<quote>' + quote_text + '</quote>\n\n'

    for br in content_copy.find_all('br'):
        br.replace_with('\n')

    text = ''
    previous_was_newline = False
    for element in content_copy.descendants:
        if isinstance(element, str):
            if '<quote>' in element:
                text += '\n\n' + element.strip() + '\n\n'
            else:
                stripped = element.strip()
                if stripped:
                    if previous_was_newline and not stripped.startswith('\n'):
                        text += stripped
                    else:
                        text += ' ' + stripped
                    previous_was_newline = False
                elif '\n' in element:
                    if not previous_was_newline:
                        text += '\n'
                        previous_was_newline = True

    text = ' '.join(text.split())
    text = text.replace(' \n', '\n').replace('\n ', '\n')
    text = text.replace('<quote>', '\n\n<quote>')
    text = text.replace('</quote>', '</quote>\n\n')
    text = text.replace('\n\n\n\n', '\n\n')
    return text

def safe_filename(title):
    return "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).rstrip()

def convert_payload(payload, out_dir):
    title = html.unescape(payload['title']).strip()
    url = payload['url']
    full_text = f"Title: {title}\nURL: {url}\n\n"
    for msg in payload['messages']:
        username = msg['usernameRaw'].split(',')[0].strip() if msg['usernameRaw'] else "Unknown User"
        content_text = process_content(msg['contentHTML'])
        full_text += f"User: {username}\n\n{content_text}\n---\n\n"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, safe_filename(title) + '.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"Saved: {out_path}\nTitle: {title}\nMessages: {len(payload['messages'])}\nBytes: {len(full_text)}")
    return out_path

def _write_finished_text(text, out_dir):
    """A bundle value that is already a finished .txt (starts with 'Title:').
    Used by the awakenetwork article extractor, which parses in-browser."""
    m = re.search(r'^Title:\s*(.+)$', text, re.M)
    title = m.group(1).strip() if m else 'untitled'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, safe_filename(title) + '.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Saved (finished text): {out_path}\nBytes: {len(text)}")
    return out_path

def _dispatch_value(v, out_dir):
    """A bundle value is a JSON string. It is EITHER a JSON payload
    {title,url,messages} (DhO) OR a finished .txt string (awakenetwork)."""
    if isinstance(v, str) and v.lstrip().startswith('Title:'):
        return _write_finished_text(v, out_dir)
    try:
        payload = json.loads(v) if isinstance(v, str) else v
    except (json.JSONDecodeError, TypeError):
        if isinstance(v, str):
            return _write_finished_text(v, out_dir)
        raise
    if isinstance(payload, dict) and 'messages' in payload:
        return convert_payload(payload, out_dir)
    return None

def convert(payload_path, out_dir):
    """Accepts EITHER a single {title,url,messages} payload OR a bundle
    {cap_key: value, ...} produced by combine_download.js, where each value is a
    DhO payload or a finished awakenetwork .txt. Writes one .txt per entry."""
    with open(payload_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'messages' in data and 'title' in data:
        return [convert_payload(data, out_dir)]
    out = []
    for key, v in data.items():
        res = _dispatch_value(v, out_dir)
        if res:
            out.append(res)
        else:
            print(f"Skipped non-payload key: {key}")
    return out

if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
