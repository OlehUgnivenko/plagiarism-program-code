import itertools
from node_normalizer import BaseNodeNormalizer


class ModuleNodeCollector(BaseNodeNormalizer):
    """
    Normalize and remove all class nodes and function nodes - leave only module level nodes.
    """

    def __init__(self, *args, **kwargs):
        super(ModuleNodeCollector, self).__init__(*args, **kwargs)
        self._module_node = None

    def visit_ClassDef(self, node):
        # remove class ...
        return

    def visit_FunctionDef(self, node):
        # remove function ...
        return

    def visit_Module(self, node):
        self._module_node = node
        count = self._node_count
        self.generic_visit(node)
        node.name = '__main__'
        node.lineno = 1
        node.col_offset = 0
        node.nsubnodes = self._node_count - count
        return node

    def get_module_node(self):
        return self._module_node


class FuncNodeCollector(BaseNodeNormalizer):
    """
    Normalize and collect all function nodes.
    """

    def __init__(self, *args, **kwargs):
        super(FuncNodeCollector, self).__init__(*args, **kwargs)
        self._curr_class_names = []
        self._func_nodes = []
        self._last_node_lineno = -1

    def generic_visit(self, node):
        self._last_node_lineno = max(getattr(node, 'lineno', -1), self._last_node_lineno)
        return super(FuncNodeCollector, self).generic_visit(node)

    def visit_ClassDef(self, node):
        self._curr_class_names.append(node.name)
        self.generic_visit(node)
        self._curr_class_names.pop()
        return node

    def visit_FunctionDef(self, node):
        node.name = '.'.join(itertools.chain(self._curr_class_names, [node.name]))
        self._func_nodes.append(node)
        count = self._node_count
        self.generic_visit(node)
        node.endlineno = self._last_node_lineno
        node.nsubnodes = self._node_count - count
        return node

    def get_function_nodes(self):
        return self._func_nodes
