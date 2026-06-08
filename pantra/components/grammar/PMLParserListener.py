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


    # Enter a parse tree produced by PMLParser#tagOpen.
    def enterTagOpen(self, ctx:PMLParser.TagOpenContext):
        pass

    # Exit a parse tree produced by PMLParser#tagOpen.
    def exitTagOpen(self, ctx:PMLParser.TagOpenContext):
        pass


    # Enter a parse tree produced by PMLParser#tagClose.
    def enterTagClose(self, ctx:PMLParser.TagCloseContext):
        pass

    # Exit a parse tree produced by PMLParser#tagClose.
    def exitTagClose(self, ctx:PMLParser.TagCloseContext):
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


    # Enter a parse tree produced by PMLParser#macroOpen.
    def enterMacroOpen(self, ctx:PMLParser.MacroOpenContext):
        pass

    # Exit a parse tree produced by PMLParser#macroOpen.
    def exitMacroOpen(self, ctx:PMLParser.MacroOpenContext):
        pass


    # Enter a parse tree produced by PMLParser#macroClose.
    def enterMacroClose(self, ctx:PMLParser.MacroCloseContext):
        pass

    # Exit a parse tree produced by PMLParser#macroClose.
    def exitMacroClose(self, ctx:PMLParser.MacroCloseContext):
        pass


    # Enter a parse tree produced by PMLParser#content.
    def enterContent(self, ctx:PMLParser.ContentContext):
        pass

    # Exit a parse tree produced by PMLParser#content.
    def exitContent(self, ctx:PMLParser.ContentContext):
        pass


    # Enter a parse tree produced by PMLParser#macroInline.
    def enterMacroInline(self, ctx:PMLParser.MacroInlineContext):
        pass

    # Exit a parse tree produced by PMLParser#macroInline.
    def exitMacroInline(self, ctx:PMLParser.MacroInlineContext):
        pass


    # Enter a parse tree produced by PMLParser#macroCommand.
    def enterMacroCommand(self, ctx:PMLParser.MacroCommandContext):
        pass

    # Exit a parse tree produced by PMLParser#macroCommand.
    def exitMacroCommand(self, ctx:PMLParser.MacroCommandContext):
        pass


    # Enter a parse tree produced by PMLParser#text.
    def enterText(self, ctx:PMLParser.TextContext):
        pass

    # Exit a parse tree produced by PMLParser#text.
    def exitText(self, ctx:PMLParser.TextContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptBlock.
    def enterScriptBlock(self, ctx:PMLParser.ScriptBlockContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptBlock.
    def exitScriptBlock(self, ctx:PMLParser.ScriptBlockContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptTag.
    def enterScriptTag(self, ctx:PMLParser.ScriptTagContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptTag.
    def exitScriptTag(self, ctx:PMLParser.ScriptTagContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptAttr.
    def enterScriptAttr(self, ctx:PMLParser.ScriptAttrContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptAttr.
    def exitScriptAttr(self, ctx:PMLParser.ScriptAttrContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptName.
    def enterScriptName(self, ctx:PMLParser.ScriptNameContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptName.
    def exitScriptName(self, ctx:PMLParser.ScriptNameContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptValue.
    def enterScriptValue(self, ctx:PMLParser.ScriptValueContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptValue.
    def exitScriptValue(self, ctx:PMLParser.ScriptValueContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptText.
    def enterScriptText(self, ctx:PMLParser.ScriptTextContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptText.
    def exitScriptText(self, ctx:PMLParser.ScriptTextContext):
        pass


    # Enter a parse tree produced by PMLParser#scriptEnd.
    def enterScriptEnd(self, ctx:PMLParser.ScriptEndContext):
        pass

    # Exit a parse tree produced by PMLParser#scriptEnd.
    def exitScriptEnd(self, ctx:PMLParser.ScriptEndContext):
        pass



del PMLParser