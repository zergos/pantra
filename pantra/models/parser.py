import traceback
import xml.parsers.expat as expat
import typing
from pathlib import Path

def parse_xml(
        file_name: Path,
        start_handler: typing.Callable[[str, dict[str, typing.Any]], None],
        end_handler: typing.Callable[[str], None] | None = None,
        parser: expat.XMLParserType | None = None
):
    p = parser or expat.ParserCreate('UTF-8')
    p.StartElementHandler = start_handler
    p.EndElementHandler = end_handler
    src = None
    try:
        src = file_name.read_text()
        p.Parse(src, True)
    except expat.ExpatError:
        traceback.print_exc(limit=-1)
        if src:
            print(src.splitlines()[p.ErrorLineNumber-1])
            print(f'{file_name}> {p.ErrorLineNumber}:{p.ErrorColumnNumber}')
