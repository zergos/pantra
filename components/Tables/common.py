from __future__ import annotations

import typing
from dataclasses import dataclass, field
from core.components.htmlnode import HTMLTemplate

if typing.TYPE_CHECKING:
    from typing import *
    MapsRows = List[List['ColMap']]


@dataclass
class ColMap:
    template: HTMLTemplate = field(default=None)
    name: str = field(default_factory=str)
    title: str = field(default_factory=str)
    align: str = field(default_factory=str)
    width: str = field(default_factory=str)
    editable: bool = field(default=True)
    sortable: bool = field(default=True)
    hspan: int = field(default=1)
    vspan: int = field(default=1)
    widget: HTMLTemplate = field(default=None)


def align_by_type(t) -> str:
    if t in (int, float):
        return 'right'
    return ''


def build_maps(template: HTMLTemplate) -> MapsRows:
    H = W = 0
    maps: MapsRows = []

    def set_cell(x, y, i):
        nonlocal H, W
        item = ColMap(template=i, hspan=1, vspan=max(H - y, 1))
        if y >= H:
            # span rows on left cells
            for kx in range(x):
                for ky in reversed(range(H)):
                    if maps[ky][kx]:
                        maps[ky][kx].vspan += 1
                        break
            maps.append([None] * (x if x == W else x + 1))
            H += 1

        if x >= W:
            # span cols above
            if y > 0:
                for ky in range(y):
                    for kx in reversed(range(W)):
                        if maps[ky][kx]:
                            maps[ky][kx].vspan += 1
                            break
                    maps[ky].append(None)
            # expand under
            for ky in range(y, H):
                maps[ky].append(None)
            W += 1

        # remove row span above
        elif y > 0 and maps[y - 1][x]:
            maps[y - 1][x].vspan = 1

        maps[y][x] = item

    def gox(l: HTMLTemplate, x: int = 0, y: int = 0) -> int:
        w = 0
        for i in l:
            if i.tag_name == 'col':
                set_cell(x + w, y, i)
                w += 1
            else:
                s = goy(i, x + w, y)
                w += s
        return w > 0

    def goy(l: HTMLTemplate, x: int , y: int) -> int:
        h = 0
        for i in l:
            if i.tag_name == 'col':
                set_cell(x, y + h, i)
                h += 1
            else:
                s = gox(i, x, y + h)
                h += s
        return h > 0

    def clear(l: MapsRows):
        for r in l:
            for c in reversed(range(len(r))):
                if not r[c]:
                    del r[c]

    gox(template)
    clear(maps)
    return maps