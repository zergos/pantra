# Generated from PMLParser.g4 by ANTLR 4.10.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,26,133,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,1,0,
        5,0,42,8,0,10,0,12,0,45,9,0,1,1,1,1,1,1,1,1,1,1,3,1,52,8,1,1,2,1,
        2,3,2,56,8,2,1,3,1,3,1,3,5,3,61,8,3,10,3,12,3,64,9,3,1,3,1,3,1,4,
        1,4,1,4,1,4,1,5,1,5,1,5,3,5,75,8,5,1,6,1,6,1,6,5,6,80,8,6,10,6,12,
        6,83,9,6,1,7,1,7,1,8,1,8,3,8,89,8,8,1,9,1,9,1,9,1,9,1,10,1,10,1,
        10,1,10,1,11,1,11,1,11,1,11,1,12,1,12,1,13,1,13,5,13,107,8,13,10,
        13,12,13,110,9,13,1,13,1,13,3,13,114,8,13,1,13,1,13,1,14,1,14,1,
        15,1,15,1,15,3,15,123,8,15,1,16,1,16,1,17,1,17,1,18,1,18,1,19,1,
        19,1,19,0,0,20,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,
        36,38,0,1,1,0,11,12,125,0,43,1,0,0,0,2,51,1,0,0,0,4,55,1,0,0,0,6,
        57,1,0,0,0,8,67,1,0,0,0,10,71,1,0,0,0,12,76,1,0,0,0,14,84,1,0,0,
        0,16,88,1,0,0,0,18,90,1,0,0,0,20,94,1,0,0,0,22,98,1,0,0,0,24,102,
        1,0,0,0,26,104,1,0,0,0,28,117,1,0,0,0,30,119,1,0,0,0,32,124,1,0,
        0,0,34,126,1,0,0,0,36,128,1,0,0,0,38,130,1,0,0,0,40,42,3,2,1,0,41,
        40,1,0,0,0,42,45,1,0,0,0,43,41,1,0,0,0,43,44,1,0,0,0,44,1,1,0,0,
        0,45,43,1,0,0,0,46,52,3,4,2,0,47,52,3,16,8,0,48,52,3,22,11,0,49,
        52,3,24,12,0,50,52,3,26,13,0,51,46,1,0,0,0,51,47,1,0,0,0,51,48,1,
        0,0,0,51,49,1,0,0,0,51,50,1,0,0,0,52,3,1,0,0,0,53,56,3,6,3,0,54,
        56,3,8,4,0,55,53,1,0,0,0,55,54,1,0,0,0,56,5,1,0,0,0,57,58,5,5,0,
        0,58,62,5,16,0,0,59,61,3,10,5,0,60,59,1,0,0,0,61,64,1,0,0,0,62,60,
        1,0,0,0,62,63,1,0,0,0,63,65,1,0,0,0,64,62,1,0,0,0,65,66,7,0,0,0,
        66,7,1,0,0,0,67,68,5,6,0,0,68,69,5,16,0,0,69,70,5,11,0,0,70,9,1,
        0,0,0,71,74,3,12,6,0,72,73,5,13,0,0,73,75,3,14,7,0,74,72,1,0,0,0,
        74,75,1,0,0,0,75,11,1,0,0,0,76,81,5,16,0,0,77,78,5,14,0,0,78,80,
        5,16,0,0,79,77,1,0,0,0,80,83,1,0,0,0,81,79,1,0,0,0,81,82,1,0,0,0,
        82,13,1,0,0,0,83,81,1,0,0,0,84,85,5,15,0,0,85,15,1,0,0,0,86,89,3,
        18,9,0,87,89,3,20,10,0,88,86,1,0,0,0,88,87,1,0,0,0,89,17,1,0,0,0,
        90,91,5,7,0,0,91,92,5,19,0,0,92,93,5,18,0,0,93,19,1,0,0,0,94,95,
        5,8,0,0,95,96,5,19,0,0,96,97,5,18,0,0,97,21,1,0,0,0,98,99,5,9,0,
        0,99,100,5,19,0,0,100,101,5,18,0,0,101,23,1,0,0,0,102,103,5,10,0,
        0,103,25,1,0,0,0,104,108,3,28,14,0,105,107,3,30,15,0,106,105,1,0,
        0,0,107,110,1,0,0,0,108,106,1,0,0,0,108,109,1,0,0,0,109,111,1,0,
        0,0,110,108,1,0,0,0,111,113,5,20,0,0,112,114,3,36,18,0,113,112,1,
        0,0,0,113,114,1,0,0,0,114,115,1,0,0,0,115,116,3,38,19,0,116,27,1,
        0,0,0,117,118,5,4,0,0,118,29,1,0,0,0,119,122,3,32,16,0,120,121,5,
        21,0,0,121,123,3,34,17,0,122,120,1,0,0,0,122,123,1,0,0,0,123,31,
        1,0,0,0,124,125,5,23,0,0,125,33,1,0,0,0,126,127,5,22,0,0,127,35,
        1,0,0,0,128,129,5,26,0,0,129,37,1,0,0,0,130,131,5,25,0,0,131,39,
        1,0,0,0,10,43,51,55,62,74,81,88,108,113,122
    ]

class PMLParser ( Parser ):

    grammarFileName = "PMLParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "'<'", "'</'", "<INVALID>", "'{{/'", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'/>'", "'='", "':'", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'}}'" ]

    symbolicNames = [ "<INVALID>", "COMMENT", "CDATA", "DTD", "RAW_TAG", 
                      "OPEN_BEGIN", "OPEN_END", "OPEN_MACRO_BEGIN", "OPEN_MACRO_END", 
                      "INLINE_MACRO", "TEXT", "CLOSE", "SLASH_CLOSE", "EQ", 
                      "COLON", "STRING", "NAME", "WS", "CLOSE_MACRO", "COMMAND", 
                      "RAW_CLOSE", "RAW_EQ", "RAW_STRING", "RAW_NAME", "RAW_WS", 
                      "CLOSE_TAG", "RAW_TEXT" ]

    RULE_process = 0
    RULE_atom = 1
    RULE_tag = 2
    RULE_tagBegin = 3
    RULE_tagEnd = 4
    RULE_attr = 5
    RULE_attrName = 6
    RULE_attrValue = 7
    RULE_macro = 8
    RULE_macroBegin = 9
    RULE_macroEnd = 10
    RULE_inlineMacro = 11
    RULE_text = 12
    RULE_rawBlock = 13
    RULE_rawTag = 14
    RULE_rawAttr = 15
    RULE_rawName = 16
    RULE_rawValue = 17
    RULE_rawText = 18
    RULE_rawCloseTag = 19

    ruleNames =  [ "process", "atom", "tag", "tagBegin", "tagEnd", "attr", 
                   "attrName", "attrValue", "macro", "macroBegin", "macroEnd", 
                   "inlineMacro", "text", "rawBlock", "rawTag", "rawAttr", 
                   "rawName", "rawValue", "rawText", "rawCloseTag" ]

    EOF = Token.EOF
    COMMENT=1
    CDATA=2
    DTD=3
    RAW_TAG=4
    OPEN_BEGIN=5
    OPEN_END=6
    OPEN_MACRO_BEGIN=7
    OPEN_MACRO_END=8
    INLINE_MACRO=9
    TEXT=10
    CLOSE=11
    SLASH_CLOSE=12
    EQ=13
    COLON=14
    STRING=15
    NAME=16
    WS=17
    CLOSE_MACRO=18
    COMMAND=19
    RAW_CLOSE=20
    RAW_EQ=21
    RAW_STRING=22
    RAW_NAME=23
    RAW_WS=24
    CLOSE_TAG=25
    RAW_TEXT=26

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.10.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProcessContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def atom(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.AtomContext)
            else:
                return self.getTypedRuleContext(PMLParser.AtomContext,i)


        def getRuleIndex(self):
            return PMLParser.RULE_process

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProcess" ):
                listener.enterProcess(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProcess" ):
                listener.exitProcess(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProcess" ):
                return visitor.visitProcess(self)
            else:
                return visitor.visitChildren(self)




    def process(self):

        localctx = PMLParser.ProcessContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_process)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PMLParser.RAW_TAG) | (1 << PMLParser.OPEN_BEGIN) | (1 << PMLParser.OPEN_END) | (1 << PMLParser.OPEN_MACRO_BEGIN) | (1 << PMLParser.OPEN_MACRO_END) | (1 << PMLParser.INLINE_MACRO) | (1 << PMLParser.TEXT))) != 0):
                self.state = 40
                self.atom()
                self.state = 45
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AtomContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def tag(self):
            return self.getTypedRuleContext(PMLParser.TagContext,0)


        def macro(self):
            return self.getTypedRuleContext(PMLParser.MacroContext,0)


        def inlineMacro(self):
            return self.getTypedRuleContext(PMLParser.InlineMacroContext,0)


        def text(self):
            return self.getTypedRuleContext(PMLParser.TextContext,0)


        def rawBlock(self):
            return self.getTypedRuleContext(PMLParser.RawBlockContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_atom

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAtom" ):
                listener.enterAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAtom" ):
                listener.exitAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtom" ):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)




    def atom(self):

        localctx = PMLParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_atom)
        try:
            self.state = 51
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.OPEN_BEGIN, PMLParser.OPEN_END]:
                self.enterOuterAlt(localctx, 1)
                self.state = 46
                self.tag()
                pass
            elif token in [PMLParser.OPEN_MACRO_BEGIN, PMLParser.OPEN_MACRO_END]:
                self.enterOuterAlt(localctx, 2)
                self.state = 47
                self.macro()
                pass
            elif token in [PMLParser.INLINE_MACRO]:
                self.enterOuterAlt(localctx, 3)
                self.state = 48
                self.inlineMacro()
                pass
            elif token in [PMLParser.TEXT]:
                self.enterOuterAlt(localctx, 4)
                self.state = 49
                self.text()
                pass
            elif token in [PMLParser.RAW_TAG]:
                self.enterOuterAlt(localctx, 5)
                self.state = 50
                self.rawBlock()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TagContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def tagBegin(self):
            return self.getTypedRuleContext(PMLParser.TagBeginContext,0)


        def tagEnd(self):
            return self.getTypedRuleContext(PMLParser.TagEndContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_tag

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTag" ):
                listener.enterTag(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTag" ):
                listener.exitTag(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTag" ):
                return visitor.visitTag(self)
            else:
                return visitor.visitChildren(self)




    def tag(self):

        localctx = PMLParser.TagContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_tag)
        try:
            self.state = 55
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.OPEN_BEGIN]:
                self.enterOuterAlt(localctx, 1)
                self.state = 53
                self.tagBegin()
                pass
            elif token in [PMLParser.OPEN_END]:
                self.enterOuterAlt(localctx, 2)
                self.state = 54
                self.tagEnd()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TagBeginContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPEN_BEGIN(self):
            return self.getToken(PMLParser.OPEN_BEGIN, 0)

        def NAME(self):
            return self.getToken(PMLParser.NAME, 0)

        def CLOSE(self):
            return self.getToken(PMLParser.CLOSE, 0)

        def SLASH_CLOSE(self):
            return self.getToken(PMLParser.SLASH_CLOSE, 0)

        def attr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.AttrContext)
            else:
                return self.getTypedRuleContext(PMLParser.AttrContext,i)


        def getRuleIndex(self):
            return PMLParser.RULE_tagBegin

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTagBegin" ):
                listener.enterTagBegin(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTagBegin" ):
                listener.exitTagBegin(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTagBegin" ):
                return visitor.visitTagBegin(self)
            else:
                return visitor.visitChildren(self)




    def tagBegin(self):

        localctx = PMLParser.TagBeginContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_tagBegin)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 57
            self.match(PMLParser.OPEN_BEGIN)
            self.state = 58
            self.match(PMLParser.NAME)
            self.state = 62
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.NAME:
                self.state = 59
                self.attr()
                self.state = 64
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 65
            _la = self._input.LA(1)
            if not(_la==PMLParser.CLOSE or _la==PMLParser.SLASH_CLOSE):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TagEndContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPEN_END(self):
            return self.getToken(PMLParser.OPEN_END, 0)

        def NAME(self):
            return self.getToken(PMLParser.NAME, 0)

        def CLOSE(self):
            return self.getToken(PMLParser.CLOSE, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_tagEnd

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTagEnd" ):
                listener.enterTagEnd(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTagEnd" ):
                listener.exitTagEnd(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTagEnd" ):
                return visitor.visitTagEnd(self)
            else:
                return visitor.visitChildren(self)




    def tagEnd(self):

        localctx = PMLParser.TagEndContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_tagEnd)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 67
            self.match(PMLParser.OPEN_END)
            self.state = 68
            self.match(PMLParser.NAME)
            self.state = 69
            self.match(PMLParser.CLOSE)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AttrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def attrName(self):
            return self.getTypedRuleContext(PMLParser.AttrNameContext,0)


        def EQ(self):
            return self.getToken(PMLParser.EQ, 0)

        def attrValue(self):
            return self.getTypedRuleContext(PMLParser.AttrValueContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_attr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAttr" ):
                listener.enterAttr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAttr" ):
                listener.exitAttr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAttr" ):
                return visitor.visitAttr(self)
            else:
                return visitor.visitChildren(self)




    def attr(self):

        localctx = PMLParser.AttrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_attr)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 71
            self.attrName()
            self.state = 74
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.EQ:
                self.state = 72
                self.match(PMLParser.EQ)
                self.state = 73
                self.attrValue()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AttrNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NAME(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.NAME)
            else:
                return self.getToken(PMLParser.NAME, i)

        def COLON(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.COLON)
            else:
                return self.getToken(PMLParser.COLON, i)

        def getRuleIndex(self):
            return PMLParser.RULE_attrName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAttrName" ):
                listener.enterAttrName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAttrName" ):
                listener.exitAttrName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAttrName" ):
                return visitor.visitAttrName(self)
            else:
                return visitor.visitChildren(self)




    def attrName(self):

        localctx = PMLParser.AttrNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_attrName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 76
            self.match(PMLParser.NAME)
            self.state = 81
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.COLON:
                self.state = 77
                self.match(PMLParser.COLON)
                self.state = 78
                self.match(PMLParser.NAME)
                self.state = 83
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AttrValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PMLParser.STRING, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_attrValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAttrValue" ):
                listener.enterAttrValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAttrValue" ):
                listener.exitAttrValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAttrValue" ):
                return visitor.visitAttrValue(self)
            else:
                return visitor.visitChildren(self)




    def attrValue(self):

        localctx = PMLParser.AttrValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_attrValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 84
            self.match(PMLParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def macroBegin(self):
            return self.getTypedRuleContext(PMLParser.MacroBeginContext,0)


        def macroEnd(self):
            return self.getTypedRuleContext(PMLParser.MacroEndContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_macro

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacro" ):
                listener.enterMacro(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacro" ):
                listener.exitMacro(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacro" ):
                return visitor.visitMacro(self)
            else:
                return visitor.visitChildren(self)




    def macro(self):

        localctx = PMLParser.MacroContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_macro)
        try:
            self.state = 88
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.OPEN_MACRO_BEGIN]:
                self.enterOuterAlt(localctx, 1)
                self.state = 86
                self.macroBegin()
                pass
            elif token in [PMLParser.OPEN_MACRO_END]:
                self.enterOuterAlt(localctx, 2)
                self.state = 87
                self.macroEnd()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroBeginContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPEN_MACRO_BEGIN(self):
            return self.getToken(PMLParser.OPEN_MACRO_BEGIN, 0)

        def COMMAND(self):
            return self.getToken(PMLParser.COMMAND, 0)

        def CLOSE_MACRO(self):
            return self.getToken(PMLParser.CLOSE_MACRO, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_macroBegin

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroBegin" ):
                listener.enterMacroBegin(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroBegin" ):
                listener.exitMacroBegin(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroBegin" ):
                return visitor.visitMacroBegin(self)
            else:
                return visitor.visitChildren(self)




    def macroBegin(self):

        localctx = PMLParser.MacroBeginContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_macroBegin)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 90
            self.match(PMLParser.OPEN_MACRO_BEGIN)
            self.state = 91
            self.match(PMLParser.COMMAND)
            self.state = 92
            self.match(PMLParser.CLOSE_MACRO)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroEndContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OPEN_MACRO_END(self):
            return self.getToken(PMLParser.OPEN_MACRO_END, 0)

        def COMMAND(self):
            return self.getToken(PMLParser.COMMAND, 0)

        def CLOSE_MACRO(self):
            return self.getToken(PMLParser.CLOSE_MACRO, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_macroEnd

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroEnd" ):
                listener.enterMacroEnd(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroEnd" ):
                listener.exitMacroEnd(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroEnd" ):
                return visitor.visitMacroEnd(self)
            else:
                return visitor.visitChildren(self)




    def macroEnd(self):

        localctx = PMLParser.MacroEndContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_macroEnd)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 94
            self.match(PMLParser.OPEN_MACRO_END)
            self.state = 95
            self.match(PMLParser.COMMAND)
            self.state = 96
            self.match(PMLParser.CLOSE_MACRO)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InlineMacroContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INLINE_MACRO(self):
            return self.getToken(PMLParser.INLINE_MACRO, 0)

        def COMMAND(self):
            return self.getToken(PMLParser.COMMAND, 0)

        def CLOSE_MACRO(self):
            return self.getToken(PMLParser.CLOSE_MACRO, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_inlineMacro

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInlineMacro" ):
                listener.enterInlineMacro(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInlineMacro" ):
                listener.exitInlineMacro(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInlineMacro" ):
                return visitor.visitInlineMacro(self)
            else:
                return visitor.visitChildren(self)




    def inlineMacro(self):

        localctx = PMLParser.InlineMacroContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_inlineMacro)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 98
            self.match(PMLParser.INLINE_MACRO)
            self.state = 99
            self.match(PMLParser.COMMAND)
            self.state = 100
            self.match(PMLParser.CLOSE_MACRO)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TextContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TEXT(self):
            return self.getToken(PMLParser.TEXT, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_text

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterText" ):
                listener.enterText(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitText" ):
                listener.exitText(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitText" ):
                return visitor.visitText(self)
            else:
                return visitor.visitChildren(self)




    def text(self):

        localctx = PMLParser.TextContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_text)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 102
            self.match(PMLParser.TEXT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawBlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def rawTag(self):
            return self.getTypedRuleContext(PMLParser.RawTagContext,0)


        def RAW_CLOSE(self):
            return self.getToken(PMLParser.RAW_CLOSE, 0)

        def rawCloseTag(self):
            return self.getTypedRuleContext(PMLParser.RawCloseTagContext,0)


        def rawAttr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.RawAttrContext)
            else:
                return self.getTypedRuleContext(PMLParser.RawAttrContext,i)


        def rawText(self):
            return self.getTypedRuleContext(PMLParser.RawTextContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_rawBlock

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawBlock" ):
                listener.enterRawBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawBlock" ):
                listener.exitRawBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawBlock" ):
                return visitor.visitRawBlock(self)
            else:
                return visitor.visitChildren(self)




    def rawBlock(self):

        localctx = PMLParser.RawBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_rawBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 104
            self.rawTag()
            self.state = 108
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.RAW_NAME:
                self.state = 105
                self.rawAttr()
                self.state = 110
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 111
            self.match(PMLParser.RAW_CLOSE)
            self.state = 113
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.RAW_TEXT:
                self.state = 112
                self.rawText()


            self.state = 115
            self.rawCloseTag()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawTagContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RAW_TAG(self):
            return self.getToken(PMLParser.RAW_TAG, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_rawTag

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawTag" ):
                listener.enterRawTag(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawTag" ):
                listener.exitRawTag(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawTag" ):
                return visitor.visitRawTag(self)
            else:
                return visitor.visitChildren(self)




    def rawTag(self):

        localctx = PMLParser.RawTagContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_rawTag)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 117
            self.match(PMLParser.RAW_TAG)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawAttrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def rawName(self):
            return self.getTypedRuleContext(PMLParser.RawNameContext,0)


        def RAW_EQ(self):
            return self.getToken(PMLParser.RAW_EQ, 0)

        def rawValue(self):
            return self.getTypedRuleContext(PMLParser.RawValueContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_rawAttr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawAttr" ):
                listener.enterRawAttr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawAttr" ):
                listener.exitRawAttr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawAttr" ):
                return visitor.visitRawAttr(self)
            else:
                return visitor.visitChildren(self)




    def rawAttr(self):

        localctx = PMLParser.RawAttrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_rawAttr)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119
            self.rawName()
            self.state = 122
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.RAW_EQ:
                self.state = 120
                self.match(PMLParser.RAW_EQ)
                self.state = 121
                self.rawValue()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RAW_NAME(self):
            return self.getToken(PMLParser.RAW_NAME, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_rawName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawName" ):
                listener.enterRawName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawName" ):
                listener.exitRawName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawName" ):
                return visitor.visitRawName(self)
            else:
                return visitor.visitChildren(self)




    def rawName(self):

        localctx = PMLParser.RawNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_rawName)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 124
            self.match(PMLParser.RAW_NAME)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RAW_STRING(self):
            return self.getToken(PMLParser.RAW_STRING, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_rawValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawValue" ):
                listener.enterRawValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawValue" ):
                listener.exitRawValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawValue" ):
                return visitor.visitRawValue(self)
            else:
                return visitor.visitChildren(self)




    def rawValue(self):

        localctx = PMLParser.RawValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_rawValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 126
            self.match(PMLParser.RAW_STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawTextContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RAW_TEXT(self):
            return self.getToken(PMLParser.RAW_TEXT, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_rawText

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawText" ):
                listener.enterRawText(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawText" ):
                listener.exitRawText(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawText" ):
                return visitor.visitRawText(self)
            else:
                return visitor.visitChildren(self)




    def rawText(self):

        localctx = PMLParser.RawTextContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_rawText)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 128
            self.match(PMLParser.RAW_TEXT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RawCloseTagContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CLOSE_TAG(self):
            return self.getToken(PMLParser.CLOSE_TAG, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_rawCloseTag

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRawCloseTag" ):
                listener.enterRawCloseTag(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRawCloseTag" ):
                listener.exitRawCloseTag(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRawCloseTag" ):
                return visitor.visitRawCloseTag(self)
            else:
                return visitor.visitChildren(self)




    def rawCloseTag(self):

        localctx = PMLParser.RawCloseTagContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_rawCloseTag)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 130
            self.match(PMLParser.CLOSE_TAG)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





