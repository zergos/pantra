// Business component definition

parser grammar BCDParser;

options { tokenVocab=BCDLexer; }

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
attrName    : NAME
            | NAME (COLON NAME)? ;
attrValue   : STRING ;

macro       : macroBegin
            | macroEnd ;
macroBegin  : OPEN_MACRO_BEGIN macroCommand CLOSE_MACRO;
macroEnd    : OPEN_MACRO_END COMMAND CLOSE_MACRO;
macroCommand: COMMAND;

inlineMacro : INLINE_MACRO COMMAND_EXP CLOSE_MACRO_EXP ;

text        : TEXT ;
rawBlock    : rawTag rawAttr* RAW_CLOSE rawText rawCloseTag ;
rawTag      : RAW_TAG ;
rawAttr     : rawName (RAW_EQ RAW_STRING)? ;
rawName     : RAW_NAME ;
rawText     : RAW_TEXT ;
rawCloseTag : CLOSE_TAG ;