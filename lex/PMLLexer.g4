// Pantra component definition

lexer grammar  PMLLexer;

// comments
COMMENT     : '<!--' .*? '-->' -> skip;
// CDATA just for XML compliance, not needed at the moment
CDATA       : '<![CDATA[' .*? ']]>' -> skip;
// DTD not needed
DTD         : '<!' .*? '>' -> skip ;

// tags with raw inner text
SCRIPT_TAG     : ('<style' | '<python' | '<script' ) ' '* -> pushMode(SCRIPT_BLOCK);

// open TAG
TAG_OPEN    : '<' -> pushMode(TAG_PROPERTIES);
TAG_CLOSE   : '</' -> pushMode(TAG_PROPERTIES);

// macro command
MACRO_OPEN
            : ('!{{#' | '{{#') -> pushMode(MACRO);
MACRO_CLOSE
            : '{{/' -> pushMode(MACRO);

MACRO_INLINE: ('{{' | '!{{') -> pushMode(MACRO);

// text content
TEXT        : ( ~[<{!] )+ ;
OTHER       : . ;

// tag definition
mode TAG_PROPERTIES;

TAG_END       : '>' -> popMode;
TAG_SLASH_END : '/>' -> popMode;
EQ            : '=' ;
COLON         : ':' ;
STRING        : '"' ~["]* '"'
              | '\'' ~[']* '\''
              | '`' ~[`]* '`';
EXPRESSION    : ([!#] | '::')* '{' ~[}]* '}'
              | ([!#] | '::')* '@' NAME ;
NUMBER        : DIGIT NameChar* ;
BOOLEAN       : 'True'
              | 'False' ;
NAME          : NameStartChar NameChar* ;
WS            : [ \t\r\n] -> skip ;

fragment
DIGIT       : [0-9] ;
fragment
NameChar    : NameStartChar
            | '-' | '.' | DIGIT | COLON
            | '\u00B7'
            | '\u0300'..'\u036F'
            | '\u203F'..'\u2040'
            ;
fragment
NameStartChar
            : [a-zA-Z_]
            | '\u2070'..'\u218F'
            | '\u2C00'..'\u2FEF'
            | '\u3001'..'\uD7FF'
            | '\uF900'..'\uFDCF'
            | '\uFDF0'..'\uFFFD'
            ;

// macro definition
mode MACRO;

MACRO_END     : '}}' -> popMode;
MACRO_COMMAND : (~[}])+ ;
MACRO_OTHER   : . ;

// raw script mode
mode SCRIPT_BLOCK;

SCRIPT_END     : '>' -> mode(SCRIPT_TEXT_MODE);
SCRIPT_EQ      : EQ ;
SCRIPT_STRING  : STRING ;
SCRIPT_NAME    : NAME ;
SCRIPT_WS      : [ \t\r\n] -> skip;

mode SCRIPT_TEXT_MODE;

SCRIPT_TEXT_END : ('</style>' | '</python>' | '</script>') -> popMode;
SCRIPT_TEXT    : (~[<])+ ;
SCRIPT_OTHER : . ;
