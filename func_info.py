import ast
import collections.abc as collections


class FuncInfo(object):
    class NonExistent(object):
        pass

    def __init__(self, func_node, code_lines):
        assert isinstance(func_node, (ast.FunctionDef, ast.Module))
        self._func_node = func_node
        self._code_lines = code_lines
        self._func_name = func_node.__dict__.pop('name', '')
        self._func_code = None
        self._func_code_lines = None
        self._func_ast = None
        self._func_ast_lines = None

    def __str__(self):
        return '<' + type(self).__name__ + ': ' + self.func_name + '>'

    @property
    def func_name(self):
        return self._func_name

    @property
    def func_node(self):
        return self._func_node

    @property
    def func_code(self):
        if self._func_code is None:
            self._func_code = ''.join(self.func_code_lines)
        return self._func_code

    @property
    def func_code_lines(self):
        if self._func_code_lines is None:
            self._func_code_lines = self._retrieve_func_code_lines(self._func_node, self._code_lines)
        return self._func_code_lines

    @property
    def func_ast(self):
        if self._func_ast is None:
            self._func_ast = self._dump(self._func_node)
        return self._func_ast

    @property
    def func_ast_lines(self):
        if self._func_ast_lines is None:
            self._func_ast_lines = self.func_ast.splitlines(True)
        return self._func_ast_lines

    @staticmethod
    def _retrieve_func_code_lines(func_node, code_lines):
        if not isinstance(func_node, (ast.FunctionDef, ast.Module)):
            return []
        if not isinstance(code_lines, collections.Sequence) or isinstance(code_lines, str):
            return []
        if getattr(func_node, 'endlineno', -1) < getattr(func_node, 'lineno', 0):
            return []
        lines = code_lines[func_node.lineno - 1: func_node.endlineno]
        if lines:
            padding = lines[0][:-len(lines[0].lstrip())]
            stripped_lines = []
            for l in lines:
                if l.startswith(padding):
                    stripped_lines.append(l[len(padding):])
                else:
                    stripped_lines = []
                    break
            if stripped_lines:
                return stripped_lines
        return lines

    @staticmethod
    def _iter_node(node, name='', missing=NonExistent):
        """Iterates over an object:
           - If the object has a _fields attribute,
             it gets attributes in the order of this
             and returns name, value pairs.
           - Otherwise, if the object is a list instance,
             it returns name, value pairs for each item
             in the list, where the name is passed into
             this function (defaults to blank).
        """
        fields = getattr(node, '_fields', None)
        if fields is not None:
            for name in fields:
                value = getattr(node, name, missing)
                if value is not missing:
                    yield value, name
        elif isinstance(node, list):
            for value in node:
                yield value, name

    @staticmethod
    def _dump(node, name=None, initial_indent='', indentation='    ',
              maxline=120, maxmerged=80, special=ast.AST):
        """Dumps an AST or similar structure:
           - Pretty-prints with indentation
           - Doesn't print line/column/ctx info
        """

        def _inner_dump(node, name=None, indent=''):
            level = indent + indentation
            name = name and name + '=' or ''
            values = list(FuncInfo._iter_node(node))
            if isinstance(node, list):
                prefix, suffix = '%s[' % name, ']'
            elif values:
                prefix, suffix = '%s%s(' % (name, type(node).__name__), ')'
            elif isinstance(node, special):
                prefix, suffix = name + type(node).__name__, ''
            else:
                return '%s%s' % (name, repr(node))
            node = [_inner_dump(a, b, level) for a, b in values if b != 'ctx']
            oneline = '%s%s%s' % (prefix, ', '.join(node), suffix)
            if len(oneline) + len(indent) < maxline:
                return '%s' % oneline
            if node and len(prefix) + len(node[0]) < maxmerged:
                prefix = '%s%s,' % (prefix, node.pop(0))
            node = (',\n%s' % level).join(node).lstrip()
            return '%s\n%s%s%s' % (prefix, level, node, suffix)

        return _inner_dump(node, name, initial_indent)
