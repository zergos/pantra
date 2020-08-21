# Generated from PMLParser.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .PMLParser import PMLParser
else:
    from PMLParser import PMLParser

# This class defines a complete generic visitor for a parse tree produced by PMLParser.

class PMLParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PMLParser#process.
    def visitProcess(self, ctx:PMLParser.ProcessContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#atom.
    def visitAtom(self, ctx:PMLParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#tag.
    def visitTag(self, ctx:PMLParser.TagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#tagBegin.
    def visitTagBegin(self, ctx:PMLParser.TagBeginContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#tagEnd.
    def visitTagEnd(self, ctx:PMLParser.TagEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#attr.
    def visitAttr(self, ctx:PMLParser.AttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#attrName.
    def visitAttrName(self, ctx:PMLParser.AttrNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#attrValue.
    def visitAttrValue(self, ctx:PMLParser.AttrValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macro.
    def visitMacro(self, ctx:PMLParser.MacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroBegin.
    def visitMacroBegin(self, ctx:PMLParser.MacroBeginContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroEnd.
    def visitMacroEnd(self, ctx:PMLParser.MacroEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroCommand.
    def visitMacroCommand(self, ctx:PMLParser.MacroCommandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#inlineMacro.
    def visitInlineMacro(self, ctx:PMLParser.InlineMacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#text.
    def visitText(self, ctx:PMLParser.TextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawBlock.
    def visitRawBlock(self, ctx:PMLParser.RawBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawTag.
    def visitRawTag(self, ctx:PMLParser.RawTagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawAttr.
    def visitRawAttr(self, ctx:PMLParser.RawAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawName.
    def visitRawName(self, ctx:PMLParser.RawNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawValue.
    def visitRawValue(self, ctx:PMLParser.RawValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawText.
    def visitRawText(self, ctx:PMLParser.RawTextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#rawCloseTag.
    def visitRawCloseTag(self, ctx:PMLParser.RawCloseTagContext):
        return self.visitChildren(ctx)



del PMLParser