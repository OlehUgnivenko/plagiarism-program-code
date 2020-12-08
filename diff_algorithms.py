import difflib
import ast
from collections import Counter


class UnifiedDiff(object):
    """
    Line diff algorithm to formatted AST string lines.
    """

    @staticmethod
    def diff(a, b):
        """
        Simpler and faster implementation of difflib.unified_diff.
        """
        assert a is not None
        assert b is not None
        a = a.func_ast_lines
        b = b.func_ast_lines

        def _gen():
            for group in difflib.SequenceMatcher(None, a, b).get_grouped_opcodes(0):
                for tag, i1, i2, j1, j2 in group:
                    if tag == 'equal':
                        for line in a[i1:i2]:
                            yield ''
                        continue
                    if tag in ('replace', 'delete'):
                        for line in a[i1:i2]:
                            yield '-'
                    if tag in ('replace', 'insert'):
                        for line in b[j1:j2]:
                            yield '+'

        return Counter(_gen())['-']

    @staticmethod
    def total(a, b):
        assert a is not None  # b may be None
        return len(a.func_ast_lines)


class TreeDiff(object):
    """
    Tree edit distance algorithm to AST.
    """

    @staticmethod
    def diff(a, b):
        assert a is not None
        assert b is not None

        def _str_dist(i, j):
            return 0 if i == j else 1

        def _get_label(n):
            return type(n).__name__

        def _get_children(n):
            if not hasattr(n, 'children'):
                n.children = list(ast.iter_child_nodes(n))
            return n.children

        import zss
        res = zss.distance(a.func_node, b.func_node, _get_children,
                           lambda node: 0,  # insert cost
                           lambda node: _str_dist(_get_label(node), ''),  # remove cost
                           lambda _a, _b: _str_dist(_get_label(_a), _get_label(_b)), )  # update cost
        return res

    @staticmethod
    def total(a, b):
        #  The count of AST nodes in referenced function
        assert a is not None  # b may be None
        return a.func_node.nsubnodes
