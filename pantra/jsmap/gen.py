import os
import json
from . import vlq

MAP_CONFIG = 'map.json'
OUT_NAME = 'all.js'


def make(path: str = '.', with_content: bool = False):
    with open(os.path.join(path, MAP_CONFIG), "rb") as f:
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
        with open(os.path.join(path, src_name), 'rt') as f:
            src = f.read()

        if with_content:
            dest['sourcesContent'].append(src)

        sl = 0
        mode = 0  # 1 - block comment /**/, 2 - string
        quote_sym = None  # '', ""
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

                    if line_started and sym in ' \t\r\n':
                        continue
                    else:
                        line_started = False

                    if not line_mapped:
                        out += ' '
                        dest['mappings'].append([len(out), src_idx, sl, sc-1])
                        line_mapped = True
                    out += sym

                elif mode == 1:
                    if sym == '*' and sc < len(line) and line[sc] == '/':
                        mode = 0
                        line_mapped = False
                        sc += 1
                        continue

                elif mode == 2:
                    out += sym
                    if sym == quote_sym:
                        if sc > 1 and line[sc-2] == '\\':
                            pass
                        elif sc < len(line) and line[sc] == quote_sym:
                            out += quote_sym
                            sc += 1
                        else:
                            mode = 0
                            continue

            sl += 1

    #for map in dest['mappings']:
    #    print(map)

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

    with open(os.path.join(path, OUT_NAME), 'wt') as f:
        f.write(out)
    with open(os.path.join(path, OUT_NAME)+'.map', 'wt') as f:
        json.dump(dest, f)


if __name__ == '__main__':
    make()
    print('done')
