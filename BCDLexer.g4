// Business component definition

lexer grammar  BCDLexer;

// comments
COMMENT     : '<!--' .*? '-->' -> skip;
// CDATA just for XML compliance, not needed at the moment
CDATA       : '<![CDATA[' .*? ']]>' -> skip;
// DTD not needed
DTD         : '<!' .*? '>' -> skip ;

// tags with raw inner text
RAW_TAG     : ('<style' | '<python') ' '* -> pushMode(RAW_BLOCK);

// open TAG
OPEN_BEGIN  : '<' -> pushMode(TAG_PROPERTIES);
OPEN_END    : '</' -> pushMode(TAG_PROPERTIES);

// macro command
OPEN_MACRO_BEGIN
            : '{#' -> pushMode(MACRO);
OPEN_MACRO_END
            : '{/' -> pushMode(MACRO);
INLINE_MACRO: '{{' -> pushMode(MACRO_EXP);

// text other content inside tags
TEXT        : (~[<{] | [{] ~[<{#/] )+ ;

mode TAG_PROPERTIES;

// close TAG
CLOSE       : '>' -> popMode;
SLASH_CLOSE : '/>' -> popMode;
EQ          : '=' ;
COLON       : ':' ;
STRING      : '"' ~["]* '"'
            | '\'' ~[']* '\'';
NAME        : NameStartChar NameChar* ;
WS          : [ \t\r\n] -> skip;

fragment
DIGIT       : [0-9] ;
fragment
NameChar    : NameStartChar
            | '-' | '.' | DIGIT
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

mode MACRO;

CLOSE_MACRO : '}' -> popMode;
COMMAND     : ~[}]+ ;


mode MACRO_EXP;

CLOSE_MACRO_EXP: '}}' -> popMode;
COMMAND_EXP    : (~[}] | [}] ~[}])+ ;

mode RAW_BLOCK;

RAW_CLOSE   : '>' -> mode(RAW_TEXT_MODE);
RAW_EQ          : EQ ;
RAW_STRING      : STRING ;
RAW_NAME    : NAME ;
RAW_WS      : [ \t\r\n] -> skip;

mode RAW_TEXT_MODE;

CLOSE_TAG   : ('</style>' | '</python>') -> popMode;
RAW_TEXT    : (~[<] | [<] ~[/] | '</' ~[ps] | '</p' ~[y] | '</s' ~[t])+ ;
//RAW_TEXT    : (~[<] | [<] ~[/] | '</' )+ ;
