# Generated from BCDParser.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .BCDParser import BCDParser
else:
    from BCDParser import BCDParser

# This class defines a complete generic visitor for a parse tree produced by BCDParser.

class BCDParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by BCDParser#process.
    def visitProcess(self, ctx:BCDParser.ProcessContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#atom.
    def visitAtom(self, ctx:BCDParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#tag.
    def visitTag(self, ctx:BCDParser.TagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#tagBegin.
    def visitTagBegin(self, ctx:BCDParser.TagBeginContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#tagEnd.
    def visitTagEnd(self, ctx:BCDParser.TagEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#attr.
    def visitAttr(self, ctx:BCDParser.AttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#attrName.
    def visitAttrName(self, ctx:BCDParser.AttrNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#attrValue.
    def visitAttrValue(self, ctx:BCDParser.AttrValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#macro.
    def visitMacro(self, ctx:BCDParser.MacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#macroBegin.
    def visitMacroBegin(self, ctx:BCDParser.MacroBeginContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#macroEnd.
    def visitMacroEnd(self, ctx:BCDParser.MacroEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#macroCommand.
    def visitMacroCommand(self, ctx:BCDParser.MacroCommandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#inlineMacro.
    def visitInlineMacro(self, ctx:BCDParser.InlineMacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#text.
    def visitText(self, ctx:BCDParser.TextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawBlock.
    def visitRawBlock(self, ctx:BCDParser.RawBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawTag.
    def visitRawTag(self, ctx:BCDParser.RawTagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawAttr.
    def visitRawAttr(self, ctx:BCDParser.RawAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawName.
    def visitRawName(self, ctx:BCDParser.RawNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawText.
    def visitRawText(self, ctx:BCDParser.RawTextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by BCDParser#rawCloseTag.
    def visitRawCloseTag(self, ctx:BCDParser.RawCloseTagContext):
        return self.visitChildren(ctx)



del BCDParser