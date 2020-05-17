# Generated from BCDParser.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .BCDParser import BCDParser
else:
    from BCDParser import BCDParser

# This class defines a complete listener for a parse tree produced by BCDParser.
class BCDParserListener(ParseTreeListener):

    # Enter a parse tree produced by BCDParser#process.
    def enterProcess(self, ctx:BCDParser.ProcessContext):
        pass

    # Exit a parse tree produced by BCDParser#process.
    def exitProcess(self, ctx:BCDParser.ProcessContext):
        pass


    # Enter a parse tree produced by BCDParser#atom.
    def enterAtom(self, ctx:BCDParser.AtomContext):
        pass

    # Exit a parse tree produced by BCDParser#atom.
    def exitAtom(self, ctx:BCDParser.AtomContext):
        pass


    # Enter a parse tree produced by BCDParser#tag.
    def enterTag(self, ctx:BCDParser.TagContext):
        pass

    # Exit a parse tree produced by BCDParser#tag.
    def exitTag(self, ctx:BCDParser.TagContext):
        pass


    # Enter a parse tree produced by BCDParser#tagBegin.
    def enterTagBegin(self, ctx:BCDParser.TagBeginContext):
        pass

    # Exit a parse tree produced by BCDParser#tagBegin.
    def exitTagBegin(self, ctx:BCDParser.TagBeginContext):
        pass


    # Enter a parse tree produced by BCDParser#tagEnd.
    def enterTagEnd(self, ctx:BCDParser.TagEndContext):
        pass

    # Exit a parse tree produced by BCDParser#tagEnd.
    def exitTagEnd(self, ctx:BCDParser.TagEndContext):
        pass


    # Enter a parse tree produced by BCDParser#attr.
    def enterAttr(self, ctx:BCDParser.AttrContext):
        pass

    # Exit a parse tree produced by BCDParser#attr.
    def exitAttr(self, ctx:BCDParser.AttrContext):
        pass


    # Enter a parse tree produced by BCDParser#attrName.
    def enterAttrName(self, ctx:BCDParser.AttrNameContext):
        pass

    # Exit a parse tree produced by BCDParser#attrName.
    def exitAttrName(self, ctx:BCDParser.AttrNameContext):
        pass


    # Enter a parse tree produced by BCDParser#attrValue.
    def enterAttrValue(self, ctx:BCDParser.AttrValueContext):
        pass

    # Exit a parse tree produced by BCDParser#attrValue.
    def exitAttrValue(self, ctx:BCDParser.AttrValueContext):
        pass


    # Enter a parse tree produced by BCDParser#macro.
    def enterMacro(self, ctx:BCDParser.MacroContext):
        pass

    # Exit a parse tree produced by BCDParser#macro.
    def exitMacro(self, ctx:BCDParser.MacroContext):
        pass


    # Enter a parse tree produced by BCDParser#macroBegin.
    def enterMacroBegin(self, ctx:BCDParser.MacroBeginContext):
        pass

    # Exit a parse tree produced by BCDParser#macroBegin.
    def exitMacroBegin(self, ctx:BCDParser.MacroBeginContext):
        pass


    # Enter a parse tree produced by BCDParser#macroEnd.
    def enterMacroEnd(self, ctx:BCDParser.MacroEndContext):
        pass

    # Exit a parse tree produced by BCDParser#macroEnd.
    def exitMacroEnd(self, ctx:BCDParser.MacroEndContext):
        pass


    # Enter a parse tree produced by BCDParser#macroCommand.
    def enterMacroCommand(self, ctx:BCDParser.MacroCommandContext):
        pass

    # Exit a parse tree produced by BCDParser#macroCommand.
    def exitMacroCommand(self, ctx:BCDParser.MacroCommandContext):
        pass


    # Enter a parse tree produced by BCDParser#inlineMacro.
    def enterInlineMacro(self, ctx:BCDParser.InlineMacroContext):
        pass

    # Exit a parse tree produced by BCDParser#inlineMacro.
    def exitInlineMacro(self, ctx:BCDParser.InlineMacroContext):
        pass


    # Enter a parse tree produced by BCDParser#text.
    def enterText(self, ctx:BCDParser.TextContext):
        pass

    # Exit a parse tree produced by BCDParser#text.
    def exitText(self, ctx:BCDParser.TextContext):
        pass


    # Enter a parse tree produced by BCDParser#rawBlock.
    def enterRawBlock(self, ctx:BCDParser.RawBlockContext):
        pass

    # Exit a parse tree produced by BCDParser#rawBlock.
    def exitRawBlock(self, ctx:BCDParser.RawBlockContext):
        pass


    # Enter a parse tree produced by BCDParser#rawTag.
    def enterRawTag(self, ctx:BCDParser.RawTagContext):
        pass

    # Exit a parse tree produced by BCDParser#rawTag.
    def exitRawTag(self, ctx:BCDParser.RawTagContext):
        pass


    # Enter a parse tree produced by BCDParser#rawAttr.
    def enterRawAttr(self, ctx:BCDParser.RawAttrContext):
        pass

    # Exit a parse tree produced by BCDParser#rawAttr.
    def exitRawAttr(self, ctx:BCDParser.RawAttrContext):
        pass


    # Enter a parse tree produced by BCDParser#rawName.
    def enterRawName(self, ctx:BCDParser.RawNameContext):
        pass

    # Exit a parse tree produced by BCDParser#rawName.
    def exitRawName(self, ctx:BCDParser.RawNameContext):
        pass


    # Enter a parse tree produced by BCDParser#rawValue.
    def enterRawValue(self, ctx:BCDParser.RawValueContext):
        pass

    # Exit a parse tree produced by BCDParser#rawValue.
    def exitRawValue(self, ctx:BCDParser.RawValueContext):
        pass


    # Enter a parse tree produced by BCDParser#rawText.
    def enterRawText(self, ctx:BCDParser.RawTextContext):
        pass

    # Exit a parse tree produced by BCDParser#rawText.
    def exitRawText(self, ctx:BCDParser.RawTextContext):
        pass


    # Enter a parse tree produced by BCDParser#rawCloseTag.
    def enterRawCloseTag(self, ctx:BCDParser.RawCloseTagContext):
        pass

    # Exit a parse tree produced by BCDParser#rawCloseTag.
    def exitRawCloseTag(self, ctx:BCDParser.RawCloseTagContext):
        pass


