import traceback
import xml.parsers.expat as expat


def parse_xml(file_name, start_handler, end_handler=None, content_handler=None, parser=None):
    p = parser or expat.ParserCreate()
    p.StartElementHandler = start_handler
    p.EndElementHandler = end_handler
    p.CharacterDataHandler = content_handler
    try:
        with open(file_name, 'rt') as f:
            src = f.read()
            p.Parse(src, True)
    except expat.ExpatError:
        traceback.print_exc(limit=-1)
        print(src.splitlines()[p.ErrorLineNumber-1])
        print(f'{file_name}> {p.ErrorLineNumber}:{p.ErrorColumnNumber}')
