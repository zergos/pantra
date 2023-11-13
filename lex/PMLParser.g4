// Pantra component definition

parser grammar PMLParser;

options { tokenVocab=PMLLexer; }

process     : atom* ;

atom        : tag
            | macro
            | inlineMacro
            | text
            | rawBlock
            ;

tag         : tagBegin
            | tagEnd
            ;
tagBegin    : OPEN_BEGIN NAME attr* (CLOSE | SLASH_CLOSE) ;
tagEnd      : OPEN_END NAME CLOSE ;

attr        : attrName (EQ attrValue)? ;
attrName    : NAME (COLON NAME)* ;
attrValue   : STRING ;

macro       : macroBegin
            | macroEnd ;
macroBegin  : OPEN_MACRO_BEGIN COMMAND CLOSE_MACRO ;
macroEnd    : OPEN_MACRO_END COMMAND CLOSE_MACRO ;

inlineMacro : INLINE_MACRO COMMAND CLOSE_MACRO ;

text        : TEXT ;
rawBlock    : rawTag rawAttr* RAW_CLOSE rawText? rawCloseTag ;
rawTag      : RAW_TAG ;
rawAttr     : rawName (RAW_EQ rawValue)? ;
rawName     : RAW_NAME ;
rawValue    : RAW_STRING ;
rawText     : RAW_TEXT ;
rawCloseTag : CLOSE_TAG ;