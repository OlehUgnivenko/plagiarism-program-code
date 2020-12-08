import ast
import collections.abc as collections


class BaseNodeNormalizer(ast.NodeTransformer):
    """
    Clean node attributes, delete the attributes that are not helpful for recognition repetition.
    """

    def __init__(self, keep_prints=False):
        super(BaseNodeNormalizer, self).__init__()
        self.keep_prints = keep_prints
        self._node_count = 0

    @staticmethod
    def _mark_docstring_sub_nodes(node):
        """
        Inspired by ast.get_docstring, mark all docstring sub nodes.
        Case1:
        regular docstring of function/class/module
        Case2:
        def foo(self):
            '''pure string expression'''
            for x in self.contents:
                '''pure string expression'''
                print x
            if self.abc:
                '''pure string expression'''
                pass
        Case3:
        def foo(self):
            if self.abc:
                print('ok')
            else:
                '''pure string expression'''
                pass
        :param node: every ast node
        :return:
        """

        def _mark_docstring_nodes(body):
            if body and isinstance(body, collections.Sequence):
                for n in body:
                    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Str):
                        n.is_docstring = True

        node_body = getattr(node, 'body', None)
        _mark_docstring_nodes(node_body)
        node_orelse = getattr(node, 'orelse', None)
        _mark_docstring_nodes(node_orelse)

    @staticmethod
    def _is_docstring(node):
        return getattr(node, 'is_docstring', False)

    def generic_visit(self, node):
        self._node_count = self._node_count + 1
        self._mark_docstring_sub_nodes(node)
        return super(BaseNodeNormalizer, self).generic_visit(node)

    def visit_Constant(self, node):
        # introduce a special value for erasing constant node value,
        # del node.value will make node.s and node.n raise Exception.
        # for Python 3.8
        dummy_value = '__pycode_similar_dummy_value__'
        if type(node) == str:
            node.value = dummy_value
        self.generic_visit(node)

    def visit_Str(self, node):
        del node.s
        self.generic_visit(node)
        return node

    def visit_Expr(self, node):
        if not self._is_docstring(node):
            self.generic_visit(node)
            if hasattr(node, 'value'):
                return node

    def visit_arg(self, node):
        """
        remove arg name & annotation for python3
        :param node: ast.arg
        :return:
        """
        del node.arg
        del node.annotation
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        del node.id
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        del node.attr
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        func = getattr(node, 'func', None)
        if not self.keep_prints and func and isinstance(func, ast.Name) and func.id == 'print':
            return  # remove print call and its sub nodes for python3
        self.generic_visit(node)
        return node

    def visit_Compare(self, node):

        def _simple_nomalize(*ops_type_names):
            if node.ops and len(node.ops) == 1 and type(node.ops[0]).__name__ in ops_type_names:
                if node.left and node.comparators and len(node.comparators) == 1:
                    left, right = node.left, node.comparators[0]
                    if type(left).__name__ > type(right).__name__:
                        left, right = right, left
                        node.left = left
                        node.comparators = [right]
                        return True
            return False

        if _simple_nomalize('Eq'):
            pass

        if _simple_nomalize('Gt', 'Lt'):
            node.ops = [{ast.Lt: ast.Gt, ast.Gt: ast.Lt}[type(node.ops[0])]()]

        if _simple_nomalize('GtE', 'LtE'):
            node.ops = [{ast.LtE: ast.GtE, ast.GtE: ast.LtE}[type(node.ops[0])]()]

        self.generic_visit(node)
        return node

    def visit_Print(self, node):
        if not self.keep_prints:
            # remove print stmt for python2
            return
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        # remove import ...
        pass

    def visit_ImportFrom(self, node):
        # remove from ... import ...
        pass
