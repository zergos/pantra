from pathlib import Path
import json
import string
from . import vlq

MAP_CONFIG = 'map.json'
OUT_NAME = 'all.js'
sepa_tokens = string.ascii_letters + string.digits + '_$'


def make(path: Path = Path('.'), with_content: bool = False, keep_spaces: bool = False):
    with (path / MAP_CONFIG).open("rb") as f:
        src_names = json.load(f)

    dest = dict(
        version=3,
        file=OUT_NAME,
        sourceRoot="",
        sources=src_names,
        names=[],
        sourcesContent=[],
        mappings=[],
    )

    out = ""
    for src_idx, src_name in enumerate(src_names):
        src = (path / src_name).read_text()

        if with_content:
            dest['sourcesContent'].append(src)

        sl = 0
        mode = 0  # 1 - block comment /**/, 2 - string
        quote_sym = None  # '', ""
        last_sym = None
        for line in src.splitlines():
            sc = 0
            line_mapped = False
            line_started = True
            while sc < len(line):
                sym = line[sc]
                sc += 1
                if mode == 0:
                    if sym in '\'"`':
                        mode = 2
                        quote_sym = sym
                        out += sym
                        continue
                    if sym == '/' and sc < len(line):
                        if line[sc] == '*':
                            mode = 1
                            sc += 1
                            continue
                        if line[sc] == '/':
                            break

                    if keep_spaces:
                        if line_started and sym in ' \t\r\n':
                            continue
                        else:
                            line_started = False
                    else:
                        if sym in ' \t\r\n':
                            line_mapped = False
                            continue

                    if not line_mapped:
                        if out and out[-1] in sepa_tokens and sym in sepa_tokens:
                            out += ' '
                        dest['mappings'].append([len(out), src_idx, sl, sc-1])
                        line_mapped = True
                    out += sym

                elif mode == 1:
                    if sym == '*' and sc < len(line) and line[sc] == '/':
                        mode = 0
                        line_mapped = False
                        sc += 1

                elif mode == 2:
                    out += sym
                    if sym == quote_sym:
                        if sc > 1 and line[sc-2] == '\\':
                            continue
                        elif sc < len(line) and line[sc] == quote_sym:
                            out += quote_sym
                            sc += 1
                        else:
                            mode = 0

            sl += 1

    mappings = []
    prev = None
    for content in dest['mappings']:
        if prev is None:
            line = content
        else:
            line = [content[i] - prev[i] for i in range(4)]
        prev = content
        mappings.append(vlq.encode(line))

    dest['mappings'] = ','.join(mappings) + ';'

    (path / OUT_NAME).write_text(out)
    with (path / (OUT_NAME + '.map')).open('wt') as f:
        json.dump(dest, f)


if __name__ == '__main__':
    if not Path(MAP_CONFIG).exists():
        print(f'define source files names list in {MAP_CONFIG} file')
    else:
        make()
        print('done')
