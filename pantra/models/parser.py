import traceback
import xml.parsers.expat as expat
import typing


def parse_xml(
        file_name: str,
        start_handler: typing.Callable[[str, dict[str, typing.Any]], None],
        end_handler: typing.Callable[[str], None] | None = None,
        parser: expat.XMLParserType | None = None
):
    p = parser or expat.ParserCreate('UTF-8')
    p.StartElementHandler = start_handler
    p.EndElementHandler = end_handler
    try:
        with open(file_name, 'rb') as f:
            src = f.read()
            p.Parse(src, True)
    except expat.ExpatError:
        traceback.print_exc(limit=-1)
        print(src.splitlines()[p.ErrorLineNumber-1])
        print(f'{file_name}> {p.ErrorLineNumber}:{p.ErrorColumnNumber}')
