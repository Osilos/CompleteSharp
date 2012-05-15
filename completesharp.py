"""
Copyright (c) 2012 Fredrik Ehnbom

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

   1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

   2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

   3. This notice may not be removed or altered from any source
   distribution.
"""
import sublime_plugin
import sublime
import os.path
import re
try:
    from sublimecompletioncommon import completioncommon
    reload(completioncommon)
except:
    def hack(func):
        # If there's a sublime.error_message before a window is open
        # on Windows 7, it appears the main editor window
        # is never opened...
        class hackClass:
            def __init__(self, func):
                self.func = func
                self.try_now()

            def try_now(self):
                if sublime.active_window() == None:
                    sublime.set_timeout(self.try_now, 500)
                else:
                    self.func()
        hackClass(func)

    def showError():
        sublime.error_message("""\
Unfortunately CompleteSharp currently can't be installed \
via Package Control. Please see http://www.github.com/quarnster/CompleteSharp \
for more details.""")
    hack(showError)


class CompleteSharpDotComplete(completioncommon.CompletionCommonDotComplete):
    pass


class CompleteSharpCompletion(completioncommon.CompletionCommon):
    def __init__(self):
        super(CompleteSharpCompletion, self).__init__("CompleteSharp.sublime-settings", os.path.dirname(os.path.abspath(__file__)))
        self.replacements = {"int": "System.Int32", "string": "System.String", "char": "System.Char", "void": "System.Void", "long": "System.Int64", "short": "System.Int16"}

    def find_absolute_of_type(self, data, full_data, type, template_args=[]):
        idx1 = type.find("+")
        idx2 = type.find("`")
        extra = ""
        if idx2 != -1 and idx1 != -1 and idx1 < idx2:
            end = type[idx2:]
            extra = type[idx1:idx2]
            type = "%s%s%s" % (type[:idx1], end, extra)
        if template_args != None and len(template_args):
            type += "`%d" % len(template_args)
        if type in self.replacements:
            type = self.replacements[type]
        return super(CompleteSharpCompletion, self).find_absolute_of_type(data, full_data, type)

    def get_packages(self, data, thispackage, type):
        packages = re.findall("[ \t]*using[ \t]+(.*);", data)
        packages.append("System")
        packages.append("")
        return packages

    def filter(self, typename, var, isstatic, data, indata):
        ret = []
        for d in indata:
            # get_ and set_ are mostly associated with properties
            if d[0].startswith("get_") or d[0].startswith("set_"):
                continue
            elif len(d) == 3 and self.is_static(d[2]) and var != None:
                continue
            ret.append(d)
        return super(CompleteSharpCompletion, self).filter(typename, var, isstatic, data, ret)

    def get_cmd(self):
        extra = self.get_setting("completesharp_assemblies", [])
        cmd = "CompleteSharp.exe \"%s\"" % ";;--;;".join(extra)
        if sublime.platform() != "windows":
            cmd = "mono " + cmd
        return cmd

    def is_supported_language(self, view):
        if view.is_scratch():
            return False
        language = self.get_language(view)
        return language == "cs"

comp = CompleteSharpCompletion()


class CompleteSharp(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        ret = comp.on_query_completions(view, prefix, locations)
        return ret

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "completesharp.dotcomplete":
            return comp.get_setting(key.replace(".", "_"), True)
        elif key == "completesharp.supported_language":
            return comp.is_supported_language(view)
        else:
            return comp.on_query_context(view, key, operator, operand, match_all)
