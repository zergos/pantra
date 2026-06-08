// Pantra component definition

parser grammar PMLParser;

options { tokenVocab=PMLLexer; }

process      : atom* ;

atom         : tag
             | macro
             | content
             | scriptBlock
             ;

tag          : tagOpen
             | tagClose
             ;
tagOpen      : TAG_OPEN NAME attr* (TAG_END | TAG_SLASH_END) ;
tagClose     : TAG_CLOSE NAME TAG_END ;

attr         : attrName (EQ attrValue)? ;
attrName     : NAME (COLON NAME)* ;
attrValue    : STRING
             | EXPRESSION
             | NUMBER
             | BOOLEAN;

macro        : macroOpen
             | macroClose ;
macroOpen    : MACRO_OPEN macroCommand MACRO_END ;
macroClose   : MACRO_CLOSE macroCommand MACRO_END ;

content	     : (macroInline | text)+ ;

macroInline  : MACRO_INLINE macroCommand MACRO_END ;

macroCommand : (MACRO_COMMAND | MACRO_OTHER)+ ;
text         : (TEXT | OTHER)+ ;
scriptBlock  : scriptTag scriptAttr* SCRIPT_END scriptText? scriptEnd ;
scriptTag    : SCRIPT_TAG ;
scriptAttr   : scriptName (SCRIPT_EQ scriptValue)? ;
scriptName   : SCRIPT_NAME ;
scriptValue  : SCRIPT_STRING ;
scriptText   : (SCRIPT_TEXT | SCRIPT_OTHER)+ ;
scriptEnd    : SCRIPT_TEXT_END ;
