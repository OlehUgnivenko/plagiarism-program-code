import ast
import operator
import argparse
from node_collector import FuncNodeCollector, ModuleNodeCollector
from func_info import FuncInfo
from diff_algorithms import TreeDiff, UnifiedDiff


class ArgParser(argparse.ArgumentParser):
    """
    A ArgumentParser to print help when got error.
    """

    def error(self, message):
        self.print_help()
        from gettext import gettext as _

        self.exit(2, _('\n%s: error: %s\n') % (self.prog, message))


class FuncDiffInfo(object):
    """
    An object stores the result of candidate python code compared to referenced python code.
    """

    info_ref = None
    info_candidate = None
    plagiarism_count = 0
    total_count = 0

    @property
    def plagiarism_percent(self):
        return 0 if self.total_count == 0 else (self.plagiarism_count / float(self.total_count))

    def __str__(self):
        if isinstance(self.info_ref, FuncInfo) and isinstance(self.info_candidate, FuncInfo):
            return '{:<4.2}: ref {}, candidate {}'.format(self.plagiarism_percent,
                                                          self.info_ref.func_name + '<' + str(
                                                                  self.info_ref.func_node.lineno) + ':' + str(
                                                                  self.info_ref.func_node.col_offset) + '>',
                                                          self.info_candidate.func_name + '<' + str(
                                                                  self.info_candidate.func_node.lineno) + ':' + str(
                                                                  self.info_candidate.func_node.col_offset) + '>')
        return '{:<4.2}: ref {}, candidate {}'.format(0, None, None)


class NoFuncException(Exception):
    def __init__(self, source):
        super(NoFuncException, self).__init__('Can not find any functions from code, index = {}'.format(source))
        self.source = source


def detect(pycode_string_list, diff_method=UnifiedDiff, keep_prints=True, module_level=False):
    if len(pycode_string_list) < 2:
        return []

    func_info_list = []
    for index, code_str in enumerate(pycode_string_list):
        root_node = ast.parse(code_str)
        collector = FuncNodeCollector(keep_prints=keep_prints)
        collector.visit(root_node)
        code_utf8_lines = code_str.splitlines(True)
        func_info = [FuncInfo(n, code_utf8_lines) for n in collector.get_function_nodes()]
        if module_level:
            root_node = ast.parse(code_str)
            collector = ModuleNodeCollector(keep_prints=keep_prints)
            collector.visit(root_node)
            module_node = collector.get_module_node()
            module_node.endlineno = len(code_utf8_lines)
            module_info = FuncInfo(module_node, code_utf8_lines)
            func_info.append(module_info)
        func_info_list.append((index, func_info))

    ast_diff_result = []
    index_ref, func_info_ref = func_info_list[0]
    if len(func_info_ref) == 0:
        raise NoFuncException(index_ref)

    for index_candidate, func_info_candidate in func_info_list[1:]:
        func_ast_diff_list = []

        for fi1 in func_info_ref:
            min_diff_value = int((1 << 31) - 1)
            min_diff_func_info = None
            for fi2 in func_info_candidate:
                dv = diff_method.diff(fi1, fi2)
                if dv < min_diff_value:
                    min_diff_value = dv
                    min_diff_func_info = fi2
                if dv == 0:  # entire function structure is plagiarized by candidate
                    break

            func_diff_info = FuncDiffInfo()
            func_diff_info.info_ref = fi1
            func_diff_info.info_candidate = min_diff_func_info
            func_diff_info.total_count = diff_method.total(fi1, min_diff_func_info)
            func_diff_info.plagiarism_count = func_diff_info.total_count - min_diff_value if min_diff_func_info else 0
            func_ast_diff_list.append(func_diff_info)
        func_ast_diff_list.sort(key=operator.attrgetter('plagiarism_percent'), reverse=True)
        ast_diff_result.append((index_candidate, func_ast_diff_list))

    return ast_diff_result


def _profile(fn):
    """
    A simple profile decorator
    :param fn: target function to be profiled
    :return: The wrapper function
    """
    import functools
    import cProfile

    @functools.wraps(fn)
    def _wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        res = fn(*args, **kwargs)
        pr.disable()
        pr.print_stats('cumulative')
        return res

    return _wrapper


def summarize(func_ast_diff_list):
    sum_total_count = sum(func_diff_info.total_count for func_diff_info in func_ast_diff_list)
    sum_plagiarism_count = sum(func_diff_info.plagiarism_count for func_diff_info in func_ast_diff_list)
    if sum_total_count == 0:
        sum_plagiarism_percent = 0
    else:
        sum_plagiarism_percent = sum_plagiarism_count / float(sum_total_count)
    return sum_plagiarism_percent, sum_plagiarism_count, sum_total_count


# @_profile
def main():
    def check_line_limit(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid line limit" % value)
        return ivalue

    def check_percentage_limit(value):
        ivalue = float(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid percentage limit" % value)
        return ivalue

    def get_file(value):
        return open(value, 'rb')

    parser = ArgParser(description='A plagiarism detection tool for python code')
    parser.add_argument('files', type=get_file, nargs=2,
                        help='the input files')
    parser.add_argument('-l', type=check_line_limit, default=4,
                        help='if AST line of the function >= value then output detail (default: 4)')
    parser.add_argument('-p', type=check_percentage_limit, default=0.5,
                        help='if plagiarism percentage of the function >= value then output detail (default: 0.5)')
    parser.add_argument('-k', '--keep-prints', action='store_true', default=False,
                        help='keep print nodes')
    parser.add_argument('-m', '--module-level', action='store_true', default=False,
                        help='process module level nodes')
    args = parser.parse_args()
    pycode_list = [(f.name, f.read()) for f in args.files]
    try:
        results = detect(
            [c[1] for c in pycode_list],
            keep_prints=args.keep_prints,
            module_level=args.module_level,
        )
    except NoFuncException as ex:
        print('error: can not find functions from {}.'.format(pycode_list[ex.source][0]))
        return

    for index, func_ast_diff_list in results:
        print('ref: {}'.format(pycode_list[0][0]))
        print('candidate: {}'.format(pycode_list[index][0]))
        sum_plagiarism_percent, sum_plagiarism_count, sum_total_count = summarize(func_ast_diff_list)
        print('{:.2f} % ({}/{}) of ref code structure is plagiarized by candidate.'.format(
            sum_plagiarism_percent * 100,
            sum_plagiarism_count,
            sum_total_count,
        ))
        print('candidate function plagiarism details (AST lines >= {} and plagiarism percentage >= {}):'.format(
            args.l,
            args.p,
        ))
        output_count = 0
        for func_diff_info in func_ast_diff_list:
            if len(func_diff_info.info_ref.func_ast_lines) >= args.l and func_diff_info.plagiarism_percent >= args.p:
                output_count = output_count + 1
                print(func_diff_info)

        if output_count == 0:
            print('<empty results>')


if __name__ == '__main__':
    main()
