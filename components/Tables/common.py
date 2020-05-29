from __future__ import annotations

import typing
import numbers
from dataclasses import dataclass, field

from core.common import DynamicStyles
from core.components.context import HTMLElement
from core.components.htmlnode import HTMLTemplate

if typing.TYPE_CHECKING:
    from typing import *
    from core.components.context import Context
    MapsRows = List[List['ColMap']]


@dataclass
class ColMap:
    node: HTMLElement = field(default=None)
    name: str = field(default_factory=str)
    title: str = field(default_factory=str)
    t: type = field(default=None)
    editable: bool = field(default=True)
    sortable: bool = field(default=True)
    resizable: bool = field(default=True)
    hspan: int = field(default=1)
    vspan: int = field(default=1)
    widget: HTMLTemplate = field(default=None)


def align_by_type(t) -> str:
    if t in (int, float):
        return 'right'
    return ''


def build_maps(ctx: Context, template: HTMLTemplate) -> MapsRows:
    H = W = 0
    maps: MapsRows = []

    def set_cell(x, y, i):
        nonlocal H, W
        item = ColMap(hspan=max(W - x, 1), vspan=max(H - y, 1))
        item.node = ctx.render.build_node(i, ctx)
        if y >= H:
            # span rows on left cells
            for kx in range(x):
                for ky in reversed(range(H)):
                    if maps[ky][kx]:
                        maps[ky][kx].vspan += 1
                        break
            maps.append([None] * W)
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

    def gox(l: HTMLTemplate, x: int = 0, y: int = 0) -> (int, int):
        w = h = 0
        for i in l:
            if i.tag_name == 'col':
                set_cell(x + w, y, i)
                w += 1
                h = max(h, 1)
            else:
                sw, sh = goy(i, x + w, y)
                w += sw
                h += sh
        return w, h

    def goy(l: HTMLTemplate, x: int, y: int) -> (int, int):
        w = h = 0
        for i in l:
            if i.tag_name == 'col':
                set_cell(x, y + h, i)
                w = max(w, 1)
                h += 1
            else:
                sw, sh = gox(i, x, y + h)
                w += sw
                h += sh
        return w, h

    def clear(l: MapsRows):
        for r in l:
            for c in reversed(range(len(r))):
                if not r[c]:
                    del r[c]

    with ctx.shot.freeze():
        gox(template)
    clear(maps)
    return maps


def collect_styles(ctx: Context, maps: MapsRows) -> (List[DynamicStyles], str):
    col_styles = []
    col_amount = max(len(row) for row in maps)
    row_amount = len(maps)
    css = []
    for i in range(col_amount):
        style = DynamicStyles()
        for y, row in enumerate(maps):
            idx = 0
            for x, c in enumerate(row):
                if c.node.style and idx <= i < idx + c.hspan:
                    td_style, col_style = c.node.style / ['width', 'background', 'border', 'visibility']
                    if td_style:
                        css.append(
                            f'#t{ctx.oid} > tbody > tr:nth-child({row_amount}n+{y + 1}) > td:nth-child({x + 1}) {{ {td_style} }}')
                    style |= col_style
                idx += c.hspan
        col_styles.append(style)
    for r in range(row_amount):
        css.append(f'#t{ctx.oid} > tbody > tr:nth-child({row_amount*2}n+{row_amount+r+1}) {{ background: rgba(160, 160, 90, 0.1) }}')
    return col_styles, '\n'.join(css)


def remove_spans(l: MapsRows):
    for r in l:
        for i in r:
            if i.hspan == 1: i.hspan = ''
            if i.vspan == 1: i.vspan = ''


def get_widget_default(t) -> str:
    if issubclass(t, numbers.Number):
        return 'CellNumber'
    else:
        return 'CellString'
