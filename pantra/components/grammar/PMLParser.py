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
        4,1,32,153,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,1,0,5,0,46,8,0,10,0,12,0,49,9,0,1,1,1,1,1,1,1,1,3,
        1,55,8,1,1,2,1,2,3,2,59,8,2,1,3,1,3,1,3,5,3,64,8,3,10,3,12,3,67,
        9,3,1,3,1,3,1,4,1,4,1,4,1,4,1,5,1,5,1,5,3,5,78,8,5,1,6,1,6,1,6,5,
        6,83,8,6,10,6,12,6,86,9,6,1,7,1,7,1,8,1,8,3,8,92,8,8,1,9,1,9,1,9,
        1,9,1,10,1,10,1,10,1,10,1,11,1,11,4,11,104,8,11,11,11,12,11,105,
        1,12,1,12,1,12,1,12,1,13,4,13,113,8,13,11,13,12,13,114,1,14,4,14,
        118,8,14,11,14,12,14,119,1,15,1,15,5,15,124,8,15,10,15,12,15,127,
        9,15,1,15,1,15,3,15,131,8,15,1,15,1,15,1,16,1,16,1,17,1,17,1,17,
        3,17,140,8,17,1,18,1,18,1,19,1,19,1,20,4,20,147,8,20,11,20,12,20,
        148,1,21,1,21,1,21,0,0,22,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,
        30,32,34,36,38,40,42,0,5,1,0,12,13,1,0,16,19,1,0,23,24,1,0,10,11,
        1,0,31,32,147,0,47,1,0,0,0,2,54,1,0,0,0,4,58,1,0,0,0,6,60,1,0,0,
        0,8,70,1,0,0,0,10,74,1,0,0,0,12,79,1,0,0,0,14,87,1,0,0,0,16,91,1,
        0,0,0,18,93,1,0,0,0,20,97,1,0,0,0,22,103,1,0,0,0,24,107,1,0,0,0,
        26,112,1,0,0,0,28,117,1,0,0,0,30,121,1,0,0,0,32,134,1,0,0,0,34,136,
        1,0,0,0,36,141,1,0,0,0,38,143,1,0,0,0,40,146,1,0,0,0,42,150,1,0,
        0,0,44,46,3,2,1,0,45,44,1,0,0,0,46,49,1,0,0,0,47,45,1,0,0,0,47,48,
        1,0,0,0,48,1,1,0,0,0,49,47,1,0,0,0,50,55,3,4,2,0,51,55,3,16,8,0,
        52,55,3,22,11,0,53,55,3,30,15,0,54,50,1,0,0,0,54,51,1,0,0,0,54,52,
        1,0,0,0,54,53,1,0,0,0,55,3,1,0,0,0,56,59,3,6,3,0,57,59,3,8,4,0,58,
        56,1,0,0,0,58,57,1,0,0,0,59,5,1,0,0,0,60,61,5,5,0,0,61,65,5,20,0,
        0,62,64,3,10,5,0,63,62,1,0,0,0,64,67,1,0,0,0,65,63,1,0,0,0,65,66,
        1,0,0,0,66,68,1,0,0,0,67,65,1,0,0,0,68,69,7,0,0,0,69,7,1,0,0,0,70,
        71,5,6,0,0,71,72,5,20,0,0,72,73,5,12,0,0,73,9,1,0,0,0,74,77,3,12,
        6,0,75,76,5,14,0,0,76,78,3,14,7,0,77,75,1,0,0,0,77,78,1,0,0,0,78,
        11,1,0,0,0,79,84,5,20,0,0,80,81,5,15,0,0,81,83,5,20,0,0,82,80,1,
        0,0,0,83,86,1,0,0,0,84,82,1,0,0,0,84,85,1,0,0,0,85,13,1,0,0,0,86,
        84,1,0,0,0,87,88,7,1,0,0,88,15,1,0,0,0,89,92,3,18,9,0,90,92,3,20,
        10,0,91,89,1,0,0,0,91,90,1,0,0,0,92,17,1,0,0,0,93,94,5,7,0,0,94,
        95,3,26,13,0,95,96,5,22,0,0,96,19,1,0,0,0,97,98,5,8,0,0,98,99,3,
        26,13,0,99,100,5,22,0,0,100,21,1,0,0,0,101,104,3,24,12,0,102,104,
        3,28,14,0,103,101,1,0,0,0,103,102,1,0,0,0,104,105,1,0,0,0,105,103,
        1,0,0,0,105,106,1,0,0,0,106,23,1,0,0,0,107,108,5,9,0,0,108,109,3,
        26,13,0,109,110,5,22,0,0,110,25,1,0,0,0,111,113,7,2,0,0,112,111,
        1,0,0,0,113,114,1,0,0,0,114,112,1,0,0,0,114,115,1,0,0,0,115,27,1,
        0,0,0,116,118,7,3,0,0,117,116,1,0,0,0,118,119,1,0,0,0,119,117,1,
        0,0,0,119,120,1,0,0,0,120,29,1,0,0,0,121,125,3,32,16,0,122,124,3,
        34,17,0,123,122,1,0,0,0,124,127,1,0,0,0,125,123,1,0,0,0,125,126,
        1,0,0,0,126,128,1,0,0,0,127,125,1,0,0,0,128,130,5,25,0,0,129,131,
        3,40,20,0,130,129,1,0,0,0,130,131,1,0,0,0,131,132,1,0,0,0,132,133,
        3,42,21,0,133,31,1,0,0,0,134,135,5,4,0,0,135,33,1,0,0,0,136,139,
        3,36,18,0,137,138,5,26,0,0,138,140,3,38,19,0,139,137,1,0,0,0,139,
        140,1,0,0,0,140,35,1,0,0,0,141,142,5,28,0,0,142,37,1,0,0,0,143,144,
        5,27,0,0,144,39,1,0,0,0,145,147,7,4,0,0,146,145,1,0,0,0,147,148,
        1,0,0,0,148,146,1,0,0,0,148,149,1,0,0,0,149,41,1,0,0,0,150,151,5,
        30,0,0,151,43,1,0,0,0,15,47,54,58,65,77,84,91,103,105,114,119,125,
        130,139,148
    ]

class PMLParser ( Parser ):

    grammarFileName = "PMLParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "'<'", "'</'", "<INVALID>", "'{{/'", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "'/>'", "'='", 
                     "':'", "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'}}'" ]

    symbolicNames = [ "<INVALID>", "COMMENT", "CDATA", "DTD", "SCRIPT_TAG", 
                      "TAG_OPEN", "TAG_CLOSE", "MACRO_OPEN", "MACRO_CLOSE", 
                      "MACRO_INLINE", "TEXT", "OTHER", "TAG_END", "TAG_SLASH_END", 
                      "EQ", "COLON", "STRING", "EXPRESSION", "NUMBER", "BOOLEAN", 
                      "NAME", "WS", "MACRO_END", "MACRO_COMMAND", "MACRO_OTHER", 
                      "SCRIPT_END", "SCRIPT_EQ", "SCRIPT_STRING", "SCRIPT_NAME", 
                      "SCRIPT_WS", "SCRIPT_TEXT_END", "SCRIPT_TEXT", "SCRIPT_OTHER" ]

    RULE_process = 0
    RULE_atom = 1
    RULE_tag = 2
    RULE_tagOpen = 3
    RULE_tagClose = 4
    RULE_attr = 5
    RULE_attrName = 6
    RULE_attrValue = 7
    RULE_macro = 8
    RULE_macroOpen = 9
    RULE_macroClose = 10
    RULE_content = 11
    RULE_macroInline = 12
    RULE_macroCommand = 13
    RULE_text = 14
    RULE_scriptBlock = 15
    RULE_scriptTag = 16
    RULE_scriptAttr = 17
    RULE_scriptName = 18
    RULE_scriptValue = 19
    RULE_scriptText = 20
    RULE_scriptEnd = 21

    ruleNames =  [ "process", "atom", "tag", "tagOpen", "tagClose", "attr", 
                   "attrName", "attrValue", "macro", "macroOpen", "macroClose", 
                   "content", "macroInline", "macroCommand", "text", "scriptBlock", 
                   "scriptTag", "scriptAttr", "scriptName", "scriptValue", 
                   "scriptText", "scriptEnd" ]

    EOF = Token.EOF
    COMMENT=1
    CDATA=2
    DTD=3
    SCRIPT_TAG=4
    TAG_OPEN=5
    TAG_CLOSE=6
    MACRO_OPEN=7
    MACRO_CLOSE=8
    MACRO_INLINE=9
    TEXT=10
    OTHER=11
    TAG_END=12
    TAG_SLASH_END=13
    EQ=14
    COLON=15
    STRING=16
    EXPRESSION=17
    NUMBER=18
    BOOLEAN=19
    NAME=20
    WS=21
    MACRO_END=22
    MACRO_COMMAND=23
    MACRO_OTHER=24
    SCRIPT_END=25
    SCRIPT_EQ=26
    SCRIPT_STRING=27
    SCRIPT_NAME=28
    SCRIPT_WS=29
    SCRIPT_TEXT_END=30
    SCRIPT_TEXT=31
    SCRIPT_OTHER=32

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
            self.state = 47
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PMLParser.SCRIPT_TAG) | (1 << PMLParser.TAG_OPEN) | (1 << PMLParser.TAG_CLOSE) | (1 << PMLParser.MACRO_OPEN) | (1 << PMLParser.MACRO_CLOSE) | (1 << PMLParser.MACRO_INLINE) | (1 << PMLParser.TEXT) | (1 << PMLParser.OTHER))) != 0):
                self.state = 44
                self.atom()
                self.state = 49
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


        def content(self):
            return self.getTypedRuleContext(PMLParser.ContentContext,0)


        def scriptBlock(self):
            return self.getTypedRuleContext(PMLParser.ScriptBlockContext,0)


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
            self.state = 54
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.TAG_OPEN, PMLParser.TAG_CLOSE]:
                self.enterOuterAlt(localctx, 1)
                self.state = 50
                self.tag()
                pass
            elif token in [PMLParser.MACRO_OPEN, PMLParser.MACRO_CLOSE]:
                self.enterOuterAlt(localctx, 2)
                self.state = 51
                self.macro()
                pass
            elif token in [PMLParser.MACRO_INLINE, PMLParser.TEXT, PMLParser.OTHER]:
                self.enterOuterAlt(localctx, 3)
                self.state = 52
                self.content()
                pass
            elif token in [PMLParser.SCRIPT_TAG]:
                self.enterOuterAlt(localctx, 4)
                self.state = 53
                self.scriptBlock()
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

        def tagOpen(self):
            return self.getTypedRuleContext(PMLParser.TagOpenContext,0)


        def tagClose(self):
            return self.getTypedRuleContext(PMLParser.TagCloseContext,0)


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
            self.state = 58
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.TAG_OPEN]:
                self.enterOuterAlt(localctx, 1)
                self.state = 56
                self.tagOpen()
                pass
            elif token in [PMLParser.TAG_CLOSE]:
                self.enterOuterAlt(localctx, 2)
                self.state = 57
                self.tagClose()
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


    class TagOpenContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TAG_OPEN(self):
            return self.getToken(PMLParser.TAG_OPEN, 0)

        def NAME(self):
            return self.getToken(PMLParser.NAME, 0)

        def TAG_END(self):
            return self.getToken(PMLParser.TAG_END, 0)

        def TAG_SLASH_END(self):
            return self.getToken(PMLParser.TAG_SLASH_END, 0)

        def attr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.AttrContext)
            else:
                return self.getTypedRuleContext(PMLParser.AttrContext,i)


        def getRuleIndex(self):
            return PMLParser.RULE_tagOpen

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTagOpen" ):
                listener.enterTagOpen(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTagOpen" ):
                listener.exitTagOpen(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTagOpen" ):
                return visitor.visitTagOpen(self)
            else:
                return visitor.visitChildren(self)




    def tagOpen(self):

        localctx = PMLParser.TagOpenContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_tagOpen)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 60
            self.match(PMLParser.TAG_OPEN)
            self.state = 61
            self.match(PMLParser.NAME)
            self.state = 65
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.NAME:
                self.state = 62
                self.attr()
                self.state = 67
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 68
            _la = self._input.LA(1)
            if not(_la==PMLParser.TAG_END or _la==PMLParser.TAG_SLASH_END):
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


    class TagCloseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TAG_CLOSE(self):
            return self.getToken(PMLParser.TAG_CLOSE, 0)

        def NAME(self):
            return self.getToken(PMLParser.NAME, 0)

        def TAG_END(self):
            return self.getToken(PMLParser.TAG_END, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_tagClose

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTagClose" ):
                listener.enterTagClose(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTagClose" ):
                listener.exitTagClose(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTagClose" ):
                return visitor.visitTagClose(self)
            else:
                return visitor.visitChildren(self)




    def tagClose(self):

        localctx = PMLParser.TagCloseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_tagClose)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 70
            self.match(PMLParser.TAG_CLOSE)
            self.state = 71
            self.match(PMLParser.NAME)
            self.state = 72
            self.match(PMLParser.TAG_END)
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
            self.state = 74
            self.attrName()
            self.state = 77
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.EQ:
                self.state = 75
                self.match(PMLParser.EQ)
                self.state = 76
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
            self.state = 79
            self.match(PMLParser.NAME)
            self.state = 84
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.COLON:
                self.state = 80
                self.match(PMLParser.COLON)
                self.state = 81
                self.match(PMLParser.NAME)
                self.state = 86
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

        def EXPRESSION(self):
            return self.getToken(PMLParser.EXPRESSION, 0)

        def NUMBER(self):
            return self.getToken(PMLParser.NUMBER, 0)

        def BOOLEAN(self):
            return self.getToken(PMLParser.BOOLEAN, 0)

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
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 87
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << PMLParser.STRING) | (1 << PMLParser.EXPRESSION) | (1 << PMLParser.NUMBER) | (1 << PMLParser.BOOLEAN))) != 0)):
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


    class MacroContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def macroOpen(self):
            return self.getTypedRuleContext(PMLParser.MacroOpenContext,0)


        def macroClose(self):
            return self.getTypedRuleContext(PMLParser.MacroCloseContext,0)


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
            self.state = 91
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [PMLParser.MACRO_OPEN]:
                self.enterOuterAlt(localctx, 1)
                self.state = 89
                self.macroOpen()
                pass
            elif token in [PMLParser.MACRO_CLOSE]:
                self.enterOuterAlt(localctx, 2)
                self.state = 90
                self.macroClose()
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


    class MacroOpenContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MACRO_OPEN(self):
            return self.getToken(PMLParser.MACRO_OPEN, 0)

        def macroCommand(self):
            return self.getTypedRuleContext(PMLParser.MacroCommandContext,0)


        def MACRO_END(self):
            return self.getToken(PMLParser.MACRO_END, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_macroOpen

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroOpen" ):
                listener.enterMacroOpen(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroOpen" ):
                listener.exitMacroOpen(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroOpen" ):
                return visitor.visitMacroOpen(self)
            else:
                return visitor.visitChildren(self)




    def macroOpen(self):

        localctx = PMLParser.MacroOpenContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_macroOpen)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 93
            self.match(PMLParser.MACRO_OPEN)
            self.state = 94
            self.macroCommand()
            self.state = 95
            self.match(PMLParser.MACRO_END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroCloseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MACRO_CLOSE(self):
            return self.getToken(PMLParser.MACRO_CLOSE, 0)

        def macroCommand(self):
            return self.getTypedRuleContext(PMLParser.MacroCommandContext,0)


        def MACRO_END(self):
            return self.getToken(PMLParser.MACRO_END, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_macroClose

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroClose" ):
                listener.enterMacroClose(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroClose" ):
                listener.exitMacroClose(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroClose" ):
                return visitor.visitMacroClose(self)
            else:
                return visitor.visitChildren(self)




    def macroClose(self):

        localctx = PMLParser.MacroCloseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_macroClose)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 97
            self.match(PMLParser.MACRO_CLOSE)
            self.state = 98
            self.macroCommand()
            self.state = 99
            self.match(PMLParser.MACRO_END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ContentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def macroInline(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.MacroInlineContext)
            else:
                return self.getTypedRuleContext(PMLParser.MacroInlineContext,i)


        def text(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.TextContext)
            else:
                return self.getTypedRuleContext(PMLParser.TextContext,i)


        def getRuleIndex(self):
            return PMLParser.RULE_content

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterContent" ):
                listener.enterContent(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitContent" ):
                listener.exitContent(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContent" ):
                return visitor.visitContent(self)
            else:
                return visitor.visitChildren(self)




    def content(self):

        localctx = PMLParser.ContentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_content)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 103 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 103
                    self._errHandler.sync(self)
                    token = self._input.LA(1)
                    if token in [PMLParser.MACRO_INLINE]:
                        self.state = 101
                        self.macroInline()
                        pass
                    elif token in [PMLParser.TEXT, PMLParser.OTHER]:
                        self.state = 102
                        self.text()
                        pass
                    else:
                        raise NoViableAltException(self)


                else:
                    raise NoViableAltException(self)
                self.state = 105 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroInlineContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MACRO_INLINE(self):
            return self.getToken(PMLParser.MACRO_INLINE, 0)

        def macroCommand(self):
            return self.getTypedRuleContext(PMLParser.MacroCommandContext,0)


        def MACRO_END(self):
            return self.getToken(PMLParser.MACRO_END, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_macroInline

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroInline" ):
                listener.enterMacroInline(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroInline" ):
                listener.exitMacroInline(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroInline" ):
                return visitor.visitMacroInline(self)
            else:
                return visitor.visitChildren(self)




    def macroInline(self):

        localctx = PMLParser.MacroInlineContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_macroInline)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 107
            self.match(PMLParser.MACRO_INLINE)
            self.state = 108
            self.macroCommand()
            self.state = 109
            self.match(PMLParser.MACRO_END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MacroCommandContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MACRO_COMMAND(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.MACRO_COMMAND)
            else:
                return self.getToken(PMLParser.MACRO_COMMAND, i)

        def MACRO_OTHER(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.MACRO_OTHER)
            else:
                return self.getToken(PMLParser.MACRO_OTHER, i)

        def getRuleIndex(self):
            return PMLParser.RULE_macroCommand

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMacroCommand" ):
                listener.enterMacroCommand(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMacroCommand" ):
                listener.exitMacroCommand(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacroCommand" ):
                return visitor.visitMacroCommand(self)
            else:
                return visitor.visitChildren(self)




    def macroCommand(self):

        localctx = PMLParser.MacroCommandContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_macroCommand)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 112 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 111
                _la = self._input.LA(1)
                if not(_la==PMLParser.MACRO_COMMAND or _la==PMLParser.MACRO_OTHER):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 114 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==PMLParser.MACRO_COMMAND or _la==PMLParser.MACRO_OTHER):
                    break

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

        def TEXT(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.TEXT)
            else:
                return self.getToken(PMLParser.TEXT, i)

        def OTHER(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.OTHER)
            else:
                return self.getToken(PMLParser.OTHER, i)

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
        self.enterRule(localctx, 28, self.RULE_text)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 117 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 116
                    _la = self._input.LA(1)
                    if not(_la==PMLParser.TEXT or _la==PMLParser.OTHER):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                else:
                    raise NoViableAltException(self)
                self.state = 119 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,10,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptBlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def scriptTag(self):
            return self.getTypedRuleContext(PMLParser.ScriptTagContext,0)


        def SCRIPT_END(self):
            return self.getToken(PMLParser.SCRIPT_END, 0)

        def scriptEnd(self):
            return self.getTypedRuleContext(PMLParser.ScriptEndContext,0)


        def scriptAttr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PMLParser.ScriptAttrContext)
            else:
                return self.getTypedRuleContext(PMLParser.ScriptAttrContext,i)


        def scriptText(self):
            return self.getTypedRuleContext(PMLParser.ScriptTextContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_scriptBlock

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptBlock" ):
                listener.enterScriptBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptBlock" ):
                listener.exitScriptBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptBlock" ):
                return visitor.visitScriptBlock(self)
            else:
                return visitor.visitChildren(self)




    def scriptBlock(self):

        localctx = PMLParser.ScriptBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_scriptBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 121
            self.scriptTag()
            self.state = 125
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==PMLParser.SCRIPT_NAME:
                self.state = 122
                self.scriptAttr()
                self.state = 127
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 128
            self.match(PMLParser.SCRIPT_END)
            self.state = 130
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.SCRIPT_TEXT or _la==PMLParser.SCRIPT_OTHER:
                self.state = 129
                self.scriptText()


            self.state = 132
            self.scriptEnd()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptTagContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SCRIPT_TAG(self):
            return self.getToken(PMLParser.SCRIPT_TAG, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_scriptTag

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptTag" ):
                listener.enterScriptTag(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptTag" ):
                listener.exitScriptTag(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptTag" ):
                return visitor.visitScriptTag(self)
            else:
                return visitor.visitChildren(self)




    def scriptTag(self):

        localctx = PMLParser.ScriptTagContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_scriptTag)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 134
            self.match(PMLParser.SCRIPT_TAG)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptAttrContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def scriptName(self):
            return self.getTypedRuleContext(PMLParser.ScriptNameContext,0)


        def SCRIPT_EQ(self):
            return self.getToken(PMLParser.SCRIPT_EQ, 0)

        def scriptValue(self):
            return self.getTypedRuleContext(PMLParser.ScriptValueContext,0)


        def getRuleIndex(self):
            return PMLParser.RULE_scriptAttr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptAttr" ):
                listener.enterScriptAttr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptAttr" ):
                listener.exitScriptAttr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptAttr" ):
                return visitor.visitScriptAttr(self)
            else:
                return visitor.visitChildren(self)




    def scriptAttr(self):

        localctx = PMLParser.ScriptAttrContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_scriptAttr)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 136
            self.scriptName()
            self.state = 139
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==PMLParser.SCRIPT_EQ:
                self.state = 137
                self.match(PMLParser.SCRIPT_EQ)
                self.state = 138
                self.scriptValue()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SCRIPT_NAME(self):
            return self.getToken(PMLParser.SCRIPT_NAME, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_scriptName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptName" ):
                listener.enterScriptName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptName" ):
                listener.exitScriptName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptName" ):
                return visitor.visitScriptName(self)
            else:
                return visitor.visitChildren(self)




    def scriptName(self):

        localctx = PMLParser.ScriptNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_scriptName)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 141
            self.match(PMLParser.SCRIPT_NAME)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SCRIPT_STRING(self):
            return self.getToken(PMLParser.SCRIPT_STRING, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_scriptValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptValue" ):
                listener.enterScriptValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptValue" ):
                listener.exitScriptValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptValue" ):
                return visitor.visitScriptValue(self)
            else:
                return visitor.visitChildren(self)




    def scriptValue(self):

        localctx = PMLParser.ScriptValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_scriptValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 143
            self.match(PMLParser.SCRIPT_STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptTextContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SCRIPT_TEXT(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.SCRIPT_TEXT)
            else:
                return self.getToken(PMLParser.SCRIPT_TEXT, i)

        def SCRIPT_OTHER(self, i:int=None):
            if i is None:
                return self.getTokens(PMLParser.SCRIPT_OTHER)
            else:
                return self.getToken(PMLParser.SCRIPT_OTHER, i)

        def getRuleIndex(self):
            return PMLParser.RULE_scriptText

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptText" ):
                listener.enterScriptText(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptText" ):
                listener.exitScriptText(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptText" ):
                return visitor.visitScriptText(self)
            else:
                return visitor.visitChildren(self)




    def scriptText(self):

        localctx = PMLParser.ScriptTextContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_scriptText)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 146 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 145
                _la = self._input.LA(1)
                if not(_la==PMLParser.SCRIPT_TEXT or _la==PMLParser.SCRIPT_OTHER):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 148 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==PMLParser.SCRIPT_TEXT or _la==PMLParser.SCRIPT_OTHER):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ScriptEndContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SCRIPT_TEXT_END(self):
            return self.getToken(PMLParser.SCRIPT_TEXT_END, 0)

        def getRuleIndex(self):
            return PMLParser.RULE_scriptEnd

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScriptEnd" ):
                listener.enterScriptEnd(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScriptEnd" ):
                listener.exitScriptEnd(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitScriptEnd" ):
                return visitor.visitScriptEnd(self)
            else:
                return visitor.visitChildren(self)




    def scriptEnd(self):

        localctx = PMLParser.ScriptEndContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_scriptEnd)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 150
            self.match(PMLParser.SCRIPT_TEXT_END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





