# Generated from PMLParser.g4 by ANTLR 4.10.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .PMLParser import PMLParser
else:
    from PMLParser import PMLParser

# This class defines a complete listener for a parse tree produced by PMLParser.
class PMLParserListener(ParseTreeListener):

    # Enter a parse tree produced by PMLParser#process.
    def enterProcess(self, ctx:PMLParser.ProcessContext):
        pass

    # Exit a parse tree produced by PMLParser#process.
    def exitProcess(self, ctx:PMLParser.ProcessContext):
        pass


    # Enter a parse tree produced by PMLParser#atom.
    def enterAtom(self, ctx:PMLParser.AtomContext):
        pass

    # Exit a parse tree produced by PMLParser#atom.
    def exitAtom(self, ctx:PMLParser.AtomContext):
        pass


    # Enter a parse tree produced by PMLParser#tag.
    def enterTag(self, ctx:PMLParser.TagContext):
        pass

    # Exit a parse tree produced by PMLParser#tag.
    def exitTag(self, ctx:PMLParser.TagContext):
        pass


    # Enter a parse tree produced by PMLParser#tagBegin.
    def enterTagBegin(self, ctx:PMLParser.TagBeginContext):
        pass

    # Exit a parse tree produced by PMLParser#tagBegin.
    def exitTagBegin(self, ctx:PMLParser.TagBeginContext):
        pass


    # Enter a parse tree produced by PMLParser#tagEnd.
    def enterTagEnd(self, ctx:PMLParser.TagEndContext):
        pass

    # Exit a parse tree produced by PMLParser#tagEnd.
    def exitTagEnd(self, ctx:PMLParser.TagEndContext):
        pass


    # Enter a parse tree produced by PMLParser#attr.
    def enterAttr(self, ctx:PMLParser.AttrContext):
        pass

    # Exit a parse tree produced by PMLParser#attr.
    def exitAttr(self, ctx:PMLParser.AttrContext):
        pass


    # Enter a parse tree produced by PMLParser#attrName.
    def enterAttrName(self, ctx:PMLParser.AttrNameContext):
        pass

    # Exit a parse tree produced by PMLParser#attrName.
    def exitAttrName(self, ctx:PMLParser.AttrNameContext):
        pass


    # Enter a parse tree produced by PMLParser#attrValue.
    def enterAttrValue(self, ctx:PMLParser.AttrValueContext):
        pass

    # Exit a parse tree produced by PMLParser#attrValue.
    def exitAttrValue(self, ctx:PMLParser.AttrValueContext):
        pass


    # Enter a parse tree produced by PMLParser#macro.
    def enterMacro(self, ctx:PMLParser.MacroContext):
        pass

    # Exit a parse tree produced by PMLParser#macro.
    def exitMacro(self, ctx:PMLParser.MacroContext):
        pass


    # Enter a parse tree produced by PMLParser#macroBegin.
    def enterMacroBegin(self, ctx:PMLParser.MacroBeginContext):
        pass

    # Exit a parse tree produced by PMLParser#macroBegin.
    def exitMacroBegin(self, ctx:PMLParser.MacroBeginContext):
        pass


    # Enter a parse tree produced by PMLParser#macroEnd.
    def enterMacroEnd(self, ctx:PMLParser.MacroEndContext):
        pass

    # Exit a parse tree produced by PMLParser#macroEnd.
    def exitMacroEnd(self, ctx:PMLParser.MacroEndContext):
        pass


    # Enter a parse tree produced by PMLParser#inlineMacro.
    def enterInlineMacro(self, ctx:PMLParser.InlineMacroContext):
        pass

    # Exit a parse tree produced by PMLParser#inlineMacro.
    def exitInlineMacro(self, ctx:PMLParser.InlineMacroContext):
        pass


    # Enter a parse tree produced by PMLParser#text.
    def enterText(self, ctx:PMLParser.TextContext):
        pass

    # Exit a parse tree produced by PMLParser#text.
    def exitText(self, ctx:PMLParser.TextContext):
        pass


    # Enter a parse tree produced by PMLParser#rawBlock.
    def enterRawBlock(self, ctx:PMLParser.RawBlockContext):
        pass

    # Exit a parse tree produced by PMLParser#rawBlock.
    def exitRawBlock(self, ctx:PMLParser.RawBlockContext):
        pass


    # Enter a parse tree produced by PMLParser#rawTag.
    def enterRawTag(self, ctx:PMLParser.RawTagContext):
        pass

    # Exit a parse tree produced by PMLParser#rawTag.
    def exitRawTag(self, ctx:PMLParser.RawTagContext):
        pass


    # Enter a parse tree produced by PMLParser#rawAttr.
    def enterRawAttr(self, ctx:PMLParser.RawAttrContext):
        pass

    # Exit a parse tree produced by PMLParser#rawAttr.
    def exitRawAttr(self, ctx:PMLParser.RawAttrContext):
        pass


    # Enter a parse tree produced by PMLParser#rawName.
    def enterRawName(self, ctx:PMLParser.RawNameContext):
        pass

    # Exit a parse tree produced by PMLParser#rawName.
    def exitRawName(self, ctx:PMLParser.RawNameContext):
        pass


    # Enter a parse tree produced by PMLParser#rawValue.
    def enterRawValue(self, ctx:PMLParser.RawValueContext):
        pass

    # Exit a parse tree produced by PMLParser#rawValue.
    def exitRawValue(self, ctx:PMLParser.RawValueContext):
        pass


    # Enter a parse tree produced by PMLParser#rawText.
    def enterRawText(self, ctx:PMLParser.RawTextContext):
        pass

    # Exit a parse tree produced by PMLParser#rawText.
    def exitRawText(self, ctx:PMLParser.RawTextContext):
        pass


    # Enter a parse tree produced by PMLParser#rawCloseTag.
    def enterRawCloseTag(self, ctx:PMLParser.RawCloseTagContext):
        pass

    # Exit a parse tree produced by PMLParser#rawCloseTag.
    def exitRawCloseTag(self, ctx:PMLParser.RawCloseTagContext):
        pass



del PMLParser