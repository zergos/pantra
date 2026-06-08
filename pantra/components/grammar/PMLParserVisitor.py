# Generated from PMLParser.g4 by ANTLR 4.10.1
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


    # Visit a parse tree produced by PMLParser#tagOpen.
    def visitTagOpen(self, ctx:PMLParser.TagOpenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#tagClose.
    def visitTagClose(self, ctx:PMLParser.TagCloseContext):
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


    # Visit a parse tree produced by PMLParser#macroOpen.
    def visitMacroOpen(self, ctx:PMLParser.MacroOpenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroClose.
    def visitMacroClose(self, ctx:PMLParser.MacroCloseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#content.
    def visitContent(self, ctx:PMLParser.ContentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroInline.
    def visitMacroInline(self, ctx:PMLParser.MacroInlineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#macroCommand.
    def visitMacroCommand(self, ctx:PMLParser.MacroCommandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#text.
    def visitText(self, ctx:PMLParser.TextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptBlock.
    def visitScriptBlock(self, ctx:PMLParser.ScriptBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptTag.
    def visitScriptTag(self, ctx:PMLParser.ScriptTagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptAttr.
    def visitScriptAttr(self, ctx:PMLParser.ScriptAttrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptName.
    def visitScriptName(self, ctx:PMLParser.ScriptNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptValue.
    def visitScriptValue(self, ctx:PMLParser.ScriptValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptText.
    def visitScriptText(self, ctx:PMLParser.ScriptTextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PMLParser#scriptEnd.
    def visitScriptEnd(self, ctx:PMLParser.ScriptEndContext):
        return self.visitChildren(ctx)



del PMLParser