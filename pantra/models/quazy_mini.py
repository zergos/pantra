from typing import Mapping
from dataclasses import dataclass, field as data_field


@dataclass
class UX:
    #field: DBField = data_field(init=False)
    name: str = ''
    type: type = None
    title: str = ''
    width: int = None
    choices: Mapping = None
    blank: bool = False
    readonly: bool = False
    multiline: bool = False
    hidden: bool = False
    sortable: bool = True
    resizable: bool = True

    def __post_init__(self):
        if self.name and not self.title:
            self.title = self.name
