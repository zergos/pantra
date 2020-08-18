import os
from ..defaults import APPS_PATH, COMPONENTS_PATH


def collect(path, components_set):
    for root, dirs, files in os.walk(path):
        for file in files:  # type: str
            if file.endswith('html'):
                base = os.path.basename(file)
                if base[0].isupper():
                    name, _ = os.path.splitext(base)
                    components_set.add(name)


def update_dtd():
    components = set()
    collect(COMPONENTS_PATH, components)
    collect(APPS_PATH, components)
    components = sorted(list(components))

    dtd = os.path.join(COMPONENTS_PATH, 'html5.dtd')
    with open(dtd, 'rt') as f:
        src = f.read()

    res = []
    for line in src.splitlines():
        res.append(line)
        if line.startswith('<!--COMPONENTS-->'):
            res.append('<!ENTITY % components "{}">'.format('|'.join(components)))

            for c in components:
                res.append(f'<!ELEMENT {c} %Flow;>')
                print(f'> {c}')
            break

    dest = '\n'.join(res)
    with open(dtd, 'wt') as f:
        f.write(dest)
