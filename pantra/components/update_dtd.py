from pathlib import Path
from ..settings import config


def collect(path: Path, components_set: set):
    for file in path.glob("**/*.html"):
        if (name:=file.stem)[0].isupper():
            components_set.add(name)


def update_dtd():
    components = set()
    collect(config.COMPONENTS_PATH, components)
    collect(config.APPS_PATH, components)
    components = sorted(list(components))

    dtd = config.COMPONENTS_PATH / 'html5.dtd'
    src = dtd.read_text()

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
    dtd.write_text(dest)
