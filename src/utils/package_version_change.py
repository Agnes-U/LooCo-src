import filecmp
import difflib
import sys
import re
import os
import platform
if (platform.system() == 'Windows'):
    slash = "\\"
else:
    slash = r"/"

class ChangeUnit:

    def __init__(self, name, full_name, unit_type, change_type):
        assert unit_type in {"function", "method", "class", "cls_common", "global_variable"}
        assert change_type in {"add", "mod", "sub"}

        self.name = name
        self.full_name = full_name
        self.unit_type = unit_type
        self.change_type = change_type

        self.lineno_cp_list = None

    def write_lineno(self, lineno_cp_list):
        self.lineno_cp_list = lineno_cp_list

    def for_global_variable(self, sure_diff, diff_place=None):
        self.sure_diff = sure_diff
        self.diff_place = diff_place

class TwoPy:
    path1 = None
    path2 = None

    change_unit_list = []

    left_only_files = []
    right_only_files = []
    diff_files_in_left = []
    diff_files_in_right = []

    if_delete_comments = True
    del_init_py = False

    def __init__(self, py1=None, py2=None):
        self.py1 = py1
        self.py2 = py2

    def remove_redundant_comments_free_files(self):
        def remove_redundant_comments_free_files_in_a_dic(dir_path):
            remove_list = []
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    full_f = os.path.join(root, f)
                    if full_f.endswith(r"(noComments).py"):
                        remove_list.append(full_f)
            for remove_file in remove_list:
                self.__remove_comment_free_file(remove_file)

        remove_redundant_comments_free_files_in_a_dic(TwoPy.path1)
        remove_redundant_comments_free_files_in_a_dic(TwoPy.path2)

    def clear_all(self):
        TwoPy.path1 = None
        TwoPy.path2 = None
        TwoPy.change_unit_list = []

        TwoPy.left_only_files = []
        TwoPy.right_only_files = []
        TwoPy.diff_files_in_left = []
        TwoPy.diff_files_in_right = []

        TwoPy.if_delete_comments = False
        TwoPy.el_init_py = True

    def get_full_name(self, py_file_str, path_str, name):
        path_str_len = len(path_str)
        py_file_str_suffix = py_file_str[path_str_len + 1:-3]
        dot_prefix = ".".join(py_file_str_suffix.split(slash))
        full_name = dot_prefix + "." + name
        return full_name

    def set_path(self, path1, path2):

        assert TwoPy.path1 == None and TwoPy.path2 == None

        TwoPy.path1 = path1
        TwoPy.path2 = path2

    def recursion_diff_path(self):

        assert len(TwoPy.diff_files_in_left) + len(TwoPy.diff_files_in_right) + len(TwoPy.left_only_files) + len(
            TwoPy.right_only_files) == 0

        path1 = TwoPy.path1
        path2 = TwoPy.path2

        from filecmp import dircmp
        import sys

        diff_files_in_left = []
        diff_files_in_right = []
        left_only = []
        right_only = []

        def get_path_by_extension(root_dir, flag='.py'):
            paths = []
            for root, dirs, files in os.walk(root_dir):
                files = [f for f in files if not f[0] == '.']
                dirs[:] = [d for d in dirs if not d[0] == '.']
                for f in files:
                    if f.endswith(flag):
                        paths.append(os.path.join(root, f))
            return paths

        def diff_path(tmppath):
            for name in tmppath.diff_files:
                if name.endswith('.py'):
                    diff_files_in_left.append(tmppath.left + slash + name)
                    diff_files_in_right.append(tmppath.right + slash + name)
            for name_left in tmppath.left_only:
                if name_left.endswith('.py'):
                    left_only.append(tmppath.left + slash + name_left)
                elif os.path.isdir(tmppath.left + slash + name_left):
                    left_only_dir_all_pyfile = get_path_by_extension(tmppath.left + slash + name_left)
                    for file in left_only_dir_all_pyfile:
                        left_only.append(file)
            for name_right in tmppath.right_only:
                if name_right.endswith('.py'):
                    right_only.append(tmppath.right + slash + name_right)
                elif os.path.isdir(tmppath.right + slash + name_right):
                    right_only_dir_all_pyfile = get_path_by_extension(tmppath.right + slash + name_right)
                    for file in right_only_dir_all_pyfile:
                        right_only.append(file)
            for sub_dcmp in tmppath.subdirs.values():
                diff_path(sub_dcmp)

        def diff_path_without_init_py(tmppath):
            for name in tmppath.diff_files:
                if name.endswith('.py') and not name.endswith('__init__.py'):
                    diff_files_in_left.append(tmppath.left + slash + name)
                    diff_files_in_right.append(tmppath.right + slash + name)
            for name_left in tmppath.left_only:
                if name_left.endswith('.py') and not name.endswith('__init__.py'):
                    left_only.append(tmppath.left + slash + name_left)
            for name_right in tmppath.right_only:
                if name_right.endswith('.py') and not name.endswith('__init__.py'):
                    right_only.append(tmppath.right + slash + name_right)
            for sub_dcmp in tmppath.subdirs.values():
                diff_path(sub_dcmp)

        mydcmp = dircmp(path1, path2)
        if TwoPy.del_init_py == False:
            diff_path(mydcmp)
        else:
            diff_path_without_init_py(mydcmp)

        TwoPy.diff_files_in_left = diff_files_in_left
        TwoPy.diff_files_in_right = diff_files_in_right
        TwoPy.left_only_files = left_only
        TwoPy.right_only_files = right_only

    def get_only_file_sub_add_func(self):

        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files
        path1, path2 = TwoPy.path1, TwoPy.path2

        for file in add_file:
            py = file
            fname, fstart, fend = get_a_pys_func_start_end_chart(py)
            cfname, cfstart, cfend = get_a_pys_classinside_func_start_end_chart(py)
            all_name = fname + cfname
            all_full_name = []
            for func_name in all_name:
                full_name = self.get_full_name(file, path2, func_name)
                all_full_name.append(full_name)

                if (func_name in set(fname)):
                    add_unit = ChangeUnit(func_name, full_name, "function", "add")
                    idx = fname.index(func_name)
                    lineno_cp = (fstart[idx], fend[idx])
                    lineno_cp_list = [lineno_cp]
                    add_unit.write_lineno(lineno_cp_list)
                    # unit_list.append(add_unit)
                    TwoPy.change_unit_list.append(add_unit)

                else:
                    add_unit = ChangeUnit(func_name, full_name, "method", "add")
                    idx = cfname.index(func_name)
                    lineno_cp = (cfstart[idx], cfend[idx])
                    lineno_cp_list = [lineno_cp]
                    add_unit.write_lineno(lineno_cp_list)
                    # unit_list.append(add_unit)
                    TwoPy.change_unit_list.append(add_unit)

        for file in sub_file:
            py = file
            fname, fstart, fend = get_a_pys_func_start_end_chart(py)
            cfname, cfstart, cfend = get_a_pys_classinside_func_start_end_chart(py)
            all_name = fname + cfname
            all_full_name = []
            for func_name in all_name:
                full_name = self.get_full_name(file, path1, func_name)
                all_full_name.append(full_name)

                if (func_name in set(fname)):
                    sub_unit = ChangeUnit(func_name, full_name, "function", "sub")
                    idx = fname.index(func_name)
                    lineno_cp = (fstart[idx], fend[idx])
                    lineno_cp_list = [lineno_cp]
                    sub_unit.write_lineno(lineno_cp_list)
                    # unit_list.append(sub_unit)
                    TwoPy.change_unit_list.append(sub_unit)

                else:
                    sub_unit = ChangeUnit(func_name, full_name, "method", "sub")
                    idx = cfname.index(func_name)
                    lineno_cp = (cfstart[idx], cfend[idx])
                    lineno_cp_list = [lineno_cp]
                    sub_unit.write_lineno(lineno_cp_list)
                    # unit_list.append(sub_unit)
                    TwoPy.change_unit_list.append(sub_unit)

    def __get_func_change(self, py1, py2):

        def append_change_unit(py_file_str, name, unit_type, change_type):

            full_name = self.get_full_name(py_file_str, path, name)

            add_unit = ChangeUnit(name, full_name, unit_type, change_type)
            TwoPy.change_unit_list.append(add_unit)

        path1, path2 = TwoPy.path1, TwoPy.path2
        py = py1
        path = path1

        if TwoPy.if_delete_comments:
            ori_py1, ori_py2 = py1, py2
            py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

        fname1, fstart1, fend1 = get_a_pys_func_start_end_chart(py1)
        fname2, fstart2, fend2 = get_a_pys_func_start_end_chart(py2)

        cfname1, cfstart1, cfend1 = get_a_pys_classinside_func_start_end_chart(py1)
        cfname2, cfstart2, cfend2 = get_a_pys_classinside_func_start_end_chart(py2)

        if len(fname1)==0 and len(fname2)==0 and len(cfname1)==0 and len(cfname2)==0:
            diff_list = []
        else:
            diff_list = get_diff(py1, py2)
        l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)

        l_mod_f = get_mod_name(l_idx_list, fname1, fstart1, fend1)
        r_mod_f = get_mod_name(r_idx_list, fname2, fstart2, fend2)

        l_mod_method = get_mod_name(l_idx_list, cfname1, cfstart1, cfend1)
        r_mod_method = get_mod_name(r_idx_list, cfname2, cfstart2, cfend2)

        add_f = set(fname2).difference(set(fname1))
        sub_f = set(fname1).difference(set(fname2))
        mod_f = set.union(l_mod_f, r_mod_f).difference(add_f).difference(sub_f)

        add_method = set(cfname2).difference(set(cfname1))
        sub_method = set(cfname1).difference(set(cfname2))
        mod_method = set.union(l_mod_method, r_mod_method).difference(add_method).difference(sub_method)

        for unit in add_f:
            append_change_unit(py, unit, "function", "add")
        for unit in sub_f:
            append_change_unit(py, unit, "function", "sub")
        for unit in mod_f:
            append_change_unit(py, unit, "function", "mod")
        for unit in add_method:
            append_change_unit(py, unit, "method", "add")
        for unit in sub_method:
            append_change_unit(py, unit, "method", "sub")
        for unit in mod_method:
            append_change_unit(py, unit, "method", "mod")

        if TwoPy.if_delete_comments:
            self.__remove_comment_free_file(py1)
            self.__remove_comment_free_file(py2)

    def get_common_file_diff_func(self):

        path1, path2 = TwoPy.path1, TwoPy.path2
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        add_func = []
        sub_func = []
        mod_func = []

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]

            self.__get_func_change(py1, py2)
            pass

    def get_change_class_and_cls_common(self):

        path1, path2 = TwoPy.path1, TwoPy.path2

        # only_file-------------------------------------------------------------------------
        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files

        for py in add_file:
            cname, cstart, cend = get_a_pys_class_start_end_chart(py)
            for cls in cname:
                full_name = self.get_full_name(py, path2, cls)
                change_unit_class = ChangeUnit(cls, full_name, "class", "add")
                change_unit_cls_common = ChangeUnit(cls, full_name, "cls_common", "add")
                idx = cname.index(cls)
                lineno_cp = (cstart[idx], cend[idx])
                lineno_cp_list = [lineno_cp]
                change_unit_class.write_lineno(lineno_cp_list)
                change_unit_cls_common.write_lineno(lineno_cp_list)
                TwoPy.change_unit_list.append(change_unit_class)
                TwoPy.change_unit_list.append(change_unit_cls_common)

        for py in sub_file:
            cname, cstart, cend = get_a_pys_class_start_end_chart(py)
            for cls in cname:
                full_name = self.get_full_name(py, path1, cls)
                change_unit_class = ChangeUnit(cls, full_name, "class", "sub")
                change_unit_cls_common = ChangeUnit(cls, full_name, "cls_common", "sub")
                idx = cname.index(cls)
                lineno_cp = (cstart[idx], cend[idx])
                lineno_cp_list = [lineno_cp]
                change_unit_class.write_lineno(lineno_cp_list)
                change_unit_cls_common.write_lineno(lineno_cp_list)
                TwoPy.change_unit_list.append(change_unit_class)
                TwoPy.change_unit_list.append(change_unit_cls_common)

        # common_file-------------------------------------------------------------------------
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]
            self.__get_change_class_and_cls_common_in_common_file(py1, py2)

    def __get_change_class_and_cls_common_in_common_file(self, py1, py2):

        path1, path2 = TwoPy.path1, TwoPy.path2
        py = py1
        path = path1

        if TwoPy.if_delete_comments:
            ori_py1, ori_py2 = py1, py2
            py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

        add_cls = set()
        sub_cls = set()
        mod_cls = set()

        cname1, cstart1, cend1 = get_a_pys_class_start_end_chart(py1)
        cname2, cstart2, cend2 = get_a_pys_class_start_end_chart(py2)

        if len(cname1)==0 and len(cname2)==0:
            diff_list = []
        else:
            diff_list = get_diff(py1, py2)
        l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)

        l_mod_c = get_mod_name(l_idx_list, cname1, cstart1, cend1)
        r_mod_c = get_mod_name(r_idx_list, cname2, cstart2, cend2)

        add_cls = set(cname2).difference(set(cname1))
        sub_cls = set(cname1).difference(set(cname2))
        mod_cls = set.union(l_mod_c, r_mod_c).difference(add_cls).difference(sub_cls)

        for cls in add_cls:
            full_name = self.get_full_name(py, path, cls)
            change_unit_class = ChangeUnit(cls, full_name, "class", "add")
            change_unit_cls_common = ChangeUnit(cls, full_name, "cls_common", "add")
            TwoPy.change_unit_list.append(change_unit_class)
            TwoPy.change_unit_list.append(change_unit_cls_common)

        for cls in sub_cls:
            full_name = self.get_full_name(py, path, cls)
            change_unit_class = ChangeUnit(cls, full_name, "class", "sub")
            change_unit_cls_common = ChangeUnit(cls, full_name, "cls_common", "sub")
            TwoPy.change_unit_list.append(change_unit_class)
            TwoPy.change_unit_list.append(change_unit_cls_common)

        for cls in mod_cls:
            full_name = self.get_full_name(py, path, cls)
            change_unit_class = ChangeUnit(cls, full_name, "class", "mod")
            TwoPy.change_unit_list.append(change_unit_class)

        for cls in mod_cls:

            idx_in_chart1 = cname1.index(cls)
            idx_in_chart2 = cname2.index(cls)
            class_start_index1, class_end_index1 = cstart1[idx_in_chart1], cend1[idx_in_chart1]
            class_start_index2, class_end_index2 = cstart2[idx_in_chart2], cend2[idx_in_chart2]

            content1, content = None, None
            with open(py1, 'r', encoding='UTF-8',errors='ignore') as file:
                content1 = file.read().splitlines()
            with open(py2, 'r', encoding='UTF-8',errors='ignore') as file:
                content2 = file.read().splitlines()

            cfname1, cfstart1, cfend1 = get_inside_class_func_chart(content1, cls, class_start_index1, class_end_index1)
            assert len(cfname1) == len(cfstart1) and len(cfstart1) == len(cfend1)
            cfname2, cfstart2, cfend2 = get_inside_class_func_chart(content2, cls, class_start_index2, class_end_index2)
            assert len(cfname2) == len(cfstart2) and len(cfstart2) == len(cfend2)

            if self.__has_cls_common_change(l_idx_list, cfname1, cfstart1, cfend1, class_start_index1,
                                            class_end_index1) or self.__has_cls_common_change(r_idx_list, cfname2,
                                                                                              cfstart2, cfend2,
                                                                                              class_start_index2,
                                                                                              class_end_index2):
                full_name = self.get_full_name(py, path, cls)
                change_unit_cls_common = ChangeUnit(cls, full_name, "cls_common", "mod")
                TwoPy.change_unit_list.append(change_unit_cls_common)

        if TwoPy.if_delete_comments:
            self.__remove_comment_free_file(py1)
            self.__remove_comment_free_file(py2)

    def __has_cls_common_change(self, idx_list, method_name_list, method_start_list, method_end_list, class_start_index,
                                class_end_index):
        num = len(method_name_list)
        for idx in idx_list:
            if idx < class_start_index or idx > class_end_index:
                continue
            idx_is_in_method = False
            for i in range(num):
                if (idx >= method_start_list[i] and idx <= method_end_list[i]):
                    idx_is_in_method = True
                    break
            if idx_is_in_method == False:
                return True

        return False

    def get_change_global_variables(self):

        def get_logic_line(py):

            import ast

            logic_line_pair_set = set()  # set of two-member tuples

            content = ""
            with open(py, 'r', encoding='UTF-8') as file:
                content = file.read()

            r_node = ast.parse(content)

            for node in ast.walk(r_node):
                if isinstance(node, ast.stmt) and hasattr(node, "lineno") and hasattr(node, "end_lineno") \
                        and type(node).__name__ != "ClassDef" and type(node).__name__ != "FunctionDef" \
                        and type(node).__name__ != "If":
                    logic_line_pair_set.add((node.lineno, node.end_lineno))

            return logic_line_pair_set

        def get_diff_logic_line(diff_idx_list, logic_line_pair_set):
            diff_line_pair_set = set()
            for diff_idx in diff_idx_list:
                cnt = 0
                tmp_set = set()
                for logic_pair in logic_line_pair_set:
                    if diff_idx >= logic_pair[0] and diff_idx <= logic_pair[1]:
                        tmp_set.add(logic_pair)
                if len(tmp_set) > 1:
                    min_len = 0x3f3f3f3f
                    min_tup = None
                    for tup in tmp_set:
                        if tup[1] - tup[0] < min_len:
                            min_len = tup[1] - tup[0]
                            min_tup = tup
                    diff_line_pair_set.add(min_tup)
                else:
                    for tup in tmp_set:
                        diff_line_pair_set.add(tup)
            return diff_line_pair_set

        def get_a_gv_store_line(py, gv):

            import ast
            store_line_set = set()  # set of physics lineno

            content = ""
            with open(py, 'r', encoding='UTF-8') as file:
                content = file.read()

            r_node = ast.parse(content)

            for node in ast.walk(r_node):
                if (type(node).__name__ == "Name") and node.id == gv and isinstance(node.ctx, ast.Store):
                    store_line_set.add(node.lineno)
            return store_line_set

        def get_func_method_name_start_end_tuple_set(py):

            import ast

            class CodeVisitor(ast.NodeVisitor):

                class_name = None
                result = set()  # a member is a (function_name/method_name, lineno, end_lineno) tuple

                def __init__(self):
                    CodeVisitor.class_name = None
                    CodeVisitor.result.clear()

                def generic_visit(self, node):
                    ast.NodeVisitor.generic_visit(self, node)

                def visit_FunctionDef(self, node):
                    if CodeVisitor.class_name == None:
                        name = str(node.name)
                    else:
                        name = CodeVisitor.class_name + "." + str(node.name)
                    CodeVisitor.result.add((name, node.lineno, node.end_lineno))

                def visit_ClassDef(self, node):
                    CodeVisitor.class_name = str(node.name)
                    ast.NodeVisitor.generic_visit(self, node)
                    CodeVisitor.class_name = None

            content = ""
            with open(py, 'r', encoding='UTF-8') as file:
                content = file.read()

            r_node = ast.parse(content)
            visitor = CodeVisitor()
            visitor.visit(r_node)
            fmname_start_end_tuple_set = CodeVisitor.result

            return fmname_start_end_tuple_set

        path1, path2 = TwoPy.path1, TwoPy.path2

        # only files--------------------------------------------------------------------
        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files

        for py in add_file:
            global_v_set = self.__get_global_variables_in_a_py(py)
            for gv in global_v_set:
                full_name = self.get_full_name(py, path2, gv)
                self.__append_change_unit_for_gv(gv, full_name, "global_variable", "add", True)

        for py in sub_file:
            global_v_set = self.__get_global_variables_in_a_py(py)
            for gv in global_v_set:
                full_name = self.get_full_name(py, path1, gv)
                self.__append_change_unit_for_gv(gv, full_name, "global_variable", "sub", True)

        # common_files--------------------------------------------------------------------
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]
            global_v_set1 = self.__get_global_variables_in_a_py(py1)
            global_v_set2 = self.__get_global_variables_in_a_py(py2)

            add_gv_set = global_v_set2.difference(global_v_set1)
            sub_gv_set = global_v_set1.difference(global_v_set2)
            common_gv_set = global_v_set2.intersection(global_v_set1)

            # add sub global variable--------------------------------------------------------------------

            for gv in add_gv_set:
                full_name = self.get_full_name(py2, path2, gv)
                self.__append_change_unit_for_gv(gv, full_name, "global_variable", "add", True)

            for gv in sub_gv_set:
                full_name = self.get_full_name(py1, path1, gv)
                self.__append_change_unit_for_gv(gv, full_name, "global_variable", "sub", True)

            # common global variable--------------------------------------------------------------------

            py = py1
            path = path1

            if TwoPy.if_delete_comments:
                ori_py1, ori_py2 = py1, py2
                py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

            change_gv_set = set()

            #  part1
            if len(common_gv_set)==0:
                diff_list = []
            else:
                diff_list = get_diff(py1, py2)
            l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)
            l_logic_line_pair_set, r_logic_line_pair_set = get_logic_line(py1), get_logic_line(py2)
            # print(py1)
            l_diff_logic_line_pair_set = get_diff_logic_line(l_idx_list, l_logic_line_pair_set)
            # print(py2)
            r_diff_logic_line_pair_set = get_diff_logic_line(r_idx_list, r_logic_line_pair_set)

            #  part2
            l_gv_storeline_dic, r_gv_storeline_dic = {}, {}
            l_gv_diff_storeline_dic, r_gv_diff_storeline_dic = {}, {}
            for gv in common_gv_set:
                l_storeline_set, r_storeline_set = get_a_gv_store_line(py1, gv), get_a_gv_store_line(py2, gv)
                l_gv_storeline_dic[gv] = l_storeline_set
                r_gv_storeline_dic[gv] = r_storeline_set

            for gv in common_gv_set:
                # left file
                l_diff_storeline_set = set()
                store_line_set = l_gv_storeline_dic[gv]
                for diff_pair in l_diff_logic_line_pair_set:
                    for store_line in store_line_set:
                        if store_line >= diff_pair[0] and store_line <= diff_pair[1]:
                            change_gv_set.add(gv)
                            l_diff_storeline_set.add(store_line)
                if len(l_diff_storeline_set) > 0:
                    l_gv_diff_storeline_dic[gv] = l_diff_storeline_set

                # right file
                r_diff_storeline_set = set()
                store_line_set = r_gv_storeline_dic[gv]
                for diff_pair in r_diff_logic_line_pair_set:
                    for store_line in store_line_set:
                        if store_line >= diff_pair[0] and store_line <= diff_pair[1]:
                            change_gv_set.add(gv)
                            r_diff_storeline_set.add(store_line)
                if len(r_diff_storeline_set) > 0:
                    r_gv_diff_storeline_dic[gv] = r_diff_storeline_set

            # part3
            l_fmname_start_end_tuple_set = get_func_method_name_start_end_tuple_set(py1)
            r_fmname_start_end_tuple_set = get_func_method_name_start_end_tuple_set(py2)

            l_diff_gv = set(l_gv_diff_storeline_dic.keys())
            r_diff_gv = set(r_gv_diff_storeline_dic.keys())
            union_diff_gv = l_diff_gv.union(r_diff_gv)

            for gv in union_diff_gv:

                l_diff_storeline_set = r_diff_storeline_set = None
                if gv in l_gv_diff_storeline_dic:
                    l_diff_storeline_set = l_gv_diff_storeline_dic[gv]
                if gv in r_gv_diff_storeline_dic:
                    r_diff_storeline_set = r_gv_diff_storeline_dic[gv]
                assert l_diff_storeline_set != None or r_diff_storeline_set != None

                global_or_cls_common = False
                diff_func_or_method_set = set()

                if l_diff_storeline_set != None:
                    for diff_storeline in l_diff_storeline_set:
                        cnt = 0
                        for tup in l_fmname_start_end_tuple_set:
                            fmname, start_line, end_line = tup[0], tup[1], tup[2]
                            if diff_storeline >= start_line and diff_storeline <= end_line:
                                cnt += 1
                                diff_func_or_method_set.add(fmname)
                        assert cnt <= 1
                        if cnt == 0:
                            global_or_cls_common = True
                            break

                if r_diff_storeline_set != None and global_or_cls_common == False:
                    for diff_storeline in r_diff_storeline_set:
                        cnt = 0
                        for tup in r_fmname_start_end_tuple_set:
                            fmname, start_line, end_line = tup[0], tup[1], tup[2]
                            if diff_storeline >= start_line and diff_storeline <= end_line:
                                cnt += 1
                                diff_func_or_method_set.add(fmname)
                        assert cnt <= 1
                        if cnt == 0:
                            global_or_cls_common = True
                            break

                full_name = self.get_full_name(py, path, gv)
                if global_or_cls_common == True:
                    self.__append_change_unit_for_gv(gv, full_name, "global_variable", "mod", True)
                else:
                    self.__append_change_unit_for_gv(gv, full_name, "global_variable", "mod", False,
                                                     diff_func_or_method_set)

            if TwoPy.if_delete_comments:
                self.__remove_comment_free_file(py1)
                self.__remove_comment_free_file(py2)

    def __get_global_variables_in_a_py(self, py):
        res = set()

        import symtable

        content = ""
        with open(py, 'r',encoding = 'utf_8') as file:
            content = file.read()

        try:
            table = symtable.symtable(content, py, compile_type="exec")
        except (SyntaxError, ValueError):
            return []

        ident_list = list(table.get_identifiers())

        for ident in ident_list:
            if table.lookup(ident).is_imported() or table.lookup(ident).is_namespace():
                continue

            if table.lookup(ident).is_global() and table.lookup(ident).is_assigned():
                res.add(ident)

        return res

    def __get_global_variables_in_a_py_python36(self, py):

        res = set()

        import symtable

        content = ""
        with open(py, 'r') as file:
            content = file.read()

        try:
            table = symtable.symtable(content, py, compile_type="exec")
        except (SyntaxError, ValueError):
            return []

        ident_list = list(table.get_identifiers())

        for ident in ident_list:
            if table.lookup(ident).is_namespace() or table.lookup(ident).is_imported() or table.lookup(
                    ident).is_global():
                pass
            else:
                res.add(ident)

        return res

    def __append_change_unit(self, name, full_name, unit_type, change_type):
        unit = ChangeUnit(name, full_name, unit_type, change_type)
        TwoPy.change_unit_list.append(unit)

    # for global variable
    def __append_change_unit_for_gv(self, name, full_name, unit_type, change_type, sure_diff, diff_place=None):
        assert unit_type == "global_variable"
        unit = ChangeUnit(name, full_name, unit_type, change_type)
        unit.for_global_variable(sure_diff, diff_place)
        TwoPy.change_unit_list.append(unit)

    def __make_comment_free_file(self, py):
        delete_comments(py)
        comment_free_py = py[:-3] + "(noComments).py"
        return comment_free_py

    def __remove_comment_free_file(self, comment_free_py):
        import os
        os.remove(comment_free_py)

    def get_change_special_functions(self):

        path1, path2 = TwoPy.path1, TwoPy.path2

        # only files--------------------------------------------------------------------
        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files

        for py in add_file:
            sf_set = get_special_func_in_a_py(py)
            #             sf_set=self.__get_special_func_in_a_py(py)
            for sf in sf_set:
                full_name = self.get_full_name(py, path2, sf)
                self.__append_change_unit(sf, full_name, "function", "add")

        for py in sub_file:
            sf_set = get_special_func_in_a_py(py)
            #             sf_v_set=self.__get_special_func_in_a_py(py)
            for sf in sf_set:
                full_name = self.get_full_name(py, path1, sf)
                self.__append_change_unit(sf, full_name, "function", "sub")

        # common_files--------------------------------------------------------------------
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]
            special_func_set1 = get_special_func_in_a_py(py1)
            special_func_set2 = get_special_func_in_a_py(py2)

            add_sf_set = special_func_set2.difference(special_func_set1)
            sub_sf_set = special_func_set1.difference(special_func_set2)
            common_sf_set = special_func_set2.intersection(special_func_set1)

            # add sub special functions--------------------------------------------------------------------

            for sf in add_sf_set:
                full_name = self.get_full_name(py2, path2, sf)
                self.__append_change_unit(sf, full_name, "function", "add")


            for sf in sub_sf_set:
                full_name = self.get_full_name(py1, path1, sf)
                self.__append_change_unit(sf, full_name, "function", "sub")


            # common special functions--------------------------------------------------------------------

            py = py1
            path = path1

            if TwoPy.if_delete_comments:
                ori_py1, ori_py2 = py1, py2
                py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

            if len(common_sf_set)==0:
                diff_list = []
            else:
                diff_list = get_diff(py1, py2)
            l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)

            change_sf_set = set()

            for special_func in common_sf_set:
                l_sf_idx_set = get_special_func_idx_set(py1, special_func)
                r_sf_idx_set = get_special_func_idx_set(py2, special_func)
                l_idx_set, r_idx_set = set(l_idx_list), set(r_idx_list)
                if len(l_sf_idx_set.intersection(l_idx_set)) > 0 or len(r_sf_idx_set.intersection(r_idx_set)) > 0:
                    change_sf_set.add(special_func)

            for sf in change_sf_set:
                full_name = self.get_full_name(py, path, sf)
                self.__append_change_unit(sf, full_name, "function", "mod")

            if TwoPy.if_delete_comments:
                self.__remove_comment_free_file(py1)
                self.__remove_comment_free_file(py2)

    def get_change_special_methods(self):

        path1, path2 = TwoPy.path1, TwoPy.path2

        # only files--------------------------------------------------------------------
        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files

        for py in add_file:
            sf_set = get_special_method_in_a_py(py)
            for sf in sf_set:
                full_name = self.get_full_name(py, path2, sf)
                self.__append_change_unit(sf, full_name, "method", "add")

        for py in sub_file:
            sf_set = get_special_method_in_a_py(py)
            for sf in sf_set:
                full_name = self.get_full_name(py, path1, sf)
                self.__append_change_unit(sf, full_name, "method", "sub")

        # common_files--------------------------------------------------------------------
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]
            special_method_set1 = set(get_special_method_in_a_py(py1))
            special_method_set2 = set(get_special_method_in_a_py(py2))

            add_sf_set = special_method_set2.difference(special_method_set1)
            sub_sf_set = special_method_set1.difference(special_method_set2)
            common_sf_set = special_method_set2.intersection(special_method_set1)

            # add sub special methods--------------------------------------------------------------------

            for sf in add_sf_set:
                full_name = self.get_full_name(py2, path2, sf)
                self.__append_change_unit(sf, full_name, "method", "add")

            for sf in sub_sf_set:
                full_name = self.get_full_name(py1, path1, sf)
                self.__append_change_unit(sf, full_name, "method", "sub")

            # common special methods--------------------------------------------------------------------

            py = py1
            path = path1

            if TwoPy.if_delete_comments:
                ori_py1, ori_py2 = py1, py2
                py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

            if len(common_sf_set)==0:
                diff_list = []
            else:
                diff_list = get_diff(py1, py2)
            l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)

            change_sf_set = set()

            for special_method in common_sf_set:
                l_sf_idx_set = get_special_method_idx_set(py1, special_method)
                r_sf_idx_set = get_special_method_idx_set(py2, special_method)
                l_idx_set, r_idx_set = set(l_idx_list), set(r_idx_list)
                if len(l_sf_idx_set.intersection(l_idx_set)) > 0 or len(r_sf_idx_set.intersection(r_idx_set)) > 0:
                    change_sf_set.add(special_method)

            for sf in change_sf_set:
                full_name = self.get_full_name(py, path, sf)
                self.__append_change_unit(sf, full_name, "method", "mod")

            if TwoPy.if_delete_comments:
                self.__remove_comment_free_file(py1)
                self.__remove_comment_free_file(py2)

    def get_change_special_class_and_cls_common(self):

        path1, path2 = TwoPy.path1, TwoPy.path2

        # only files--------------------------------------------------------------------
        sub_file, add_file = TwoPy.left_only_files, TwoPy.right_only_files

        for py in add_file:
            sc_set = get_special_class_in_a_py(py)
            for sc in sc_set:
                full_name = self.get_full_name(py, path2, sc)
                self.__append_change_unit(sc, full_name, "class", "add")
                self.__append_change_unit(sc, full_name, "cls_common", "add")

        for py in sub_file:
            sc_set = get_special_class_in_a_py(py)
            for sc in sc_set:
                full_name = self.get_full_name(py, path1, sc)
                self.__append_change_unit(sc, full_name, "class", "sub")
                self.__append_change_unit(sc, full_name, "cls_common", "sub")

        # common_files--------------------------------------------------------------------
        diff_files_in_left, diff_files_in_right = TwoPy.diff_files_in_left, TwoPy.diff_files_in_right
        assert len(diff_files_in_left) == len(diff_files_in_right)

        for i in range(len(diff_files_in_left)):
            py1 = diff_files_in_left[i]
            py2 = diff_files_in_right[i]
            special_class_set1 = set(get_special_class_in_a_py(py1))
            special_class_set2 = set(get_special_class_in_a_py(py2))

            add_sc_set = special_class_set2.difference(special_class_set1)
            sub_sc_set = special_class_set1.difference(special_class_set2)
            common_sc_set = special_class_set2.intersection(special_class_set1)

            # add sub special methods--------------------------------------------------------------------
            for sc in add_sc_set:
                full_name = self.get_full_name(py2, path2, sc)
                self.__append_change_unit(sc, full_name, "class", "add")
                self.__append_change_unit(sc, full_name, "cls_common", "add")

            for sc in sub_sc_set:
                full_name = self.get_full_name(py1, path1, sc)
                self.__append_change_unit(sc, full_name, "class", "sub")
                self.__append_change_unit(sc, full_name, "cls_common", "sub")

            # common special methods--------------------------------------------------------------------

            py = py1
            path = path1

            if TwoPy.if_delete_comments:
                ori_py1, ori_py2 = py1, py2
                py1, py2 = self.__make_comment_free_file(py1), self.__make_comment_free_file(py2)

            if len(common_sc_set)==0:
                diff_list = []
            else:
                diff_list = get_diff(py1, py2)
            l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)

            change_sc_set = set()
            change_sc_cls_common_set = set()

            for special_class in common_sc_set:
                l_sc_idx_set = get_special_class_idx_set(py1, special_class)
                r_sc_idx_set = get_special_class_idx_set(py2, special_class)
                l_idx_set, r_idx_set = set(l_idx_list), set(r_idx_list)
                if len(l_sc_idx_set.intersection(l_idx_set)) > 0 or len(r_sc_idx_set.intersection(r_idx_set)) > 0:
                    change_sc_set.add(special_class)

                    sc = special_class
                    l_sc_method_set = get_all_methods_in_a_class(py1, sc)
                    r_sc_method_set = get_all_methods_in_a_class(py2, sc)
                    l_sc_method_idx_set, r_sc_method_idx_set = set(), set()
                    for l_sc_method in l_sc_method_set:
                        l_sc_method_idx_set = l_sc_method_idx_set.union(get_special_method_idx_set(py1, l_sc_method))
                    for r_sc_method in r_sc_method_set:
                        r_sc_method_idx_set = r_sc_method_idx_set.union(get_special_method_idx_set(py2, r_sc_method))

                    l_inside_class_diff_set = l_sc_idx_set.intersection(l_idx_set)
                    r_inside_class_diff_set = r_sc_idx_set.intersection(r_idx_set)

                    if len(l_inside_class_diff_set.difference(l_sc_method_idx_set)) > 0 or \
                            len(r_inside_class_diff_set.difference(r_sc_method_idx_set)) > 0:
                        change_sc_cls_common_set.add(special_class)

            for sc in change_sc_set:
                full_name = self.get_full_name(py, path, sc)
                self.__append_change_unit(sc, full_name, "class", "mod")

            for sc in change_sc_cls_common_set:
                full_name = self.get_full_name(py, path, sc)
                self.__append_change_unit(sc, full_name, "cls_common", "mod")

            if TwoPy.if_delete_comments:
                self.__remove_comment_free_file(py1)
                self.__remove_comment_free_file(py2)



class NameUnit:
    short_to_long_dict = {}
    long_type_dict = {}
    entry_path = None

    def __init__(self, random_name, name_type=None):
        long_name = random_name
        if random_name not in NameUnit.long_type_dict:  # random_name is a short name
            long_name = NameUnit.short_to_long_dict[random_name]
        if name_type == None:
            name_type = NameUnit.long_type_dict[long_name]

        assert name_type in ("function", "method", "class", "global_variable", \
                             "module", "middle_path")

        self.long_name = long_name
        self.name_type = name_type

    def get_long_name(self):
        return self.long_name

    def get_name_type(self):
        return self.name_type


def init_NameUnit(entry_path):
    assert NameUnit.entry_path == None

    long_type_dict = {}
    to_search = set()
    to_search.add((entry_path,))

    while len(to_search):
        root_tuple = to_search.pop()
        root_path = slash.join(root_tuple)
        children = os.listdir(root_path)
        for child in children:
            if child.find('.') == -1:
                child_tuple = root_tuple + (child,)
                middle_path_dot = ".".join(child_tuple[1:])
                long_type_dict[middle_path_dot] = "middle_path"
                to_search.add(child_tuple)
            elif child.find('.py') != -1:
                module_name = child[:-3]
                child_tuple = root_tuple + (module_name,)
                module_dot = ".".join(child_tuple[1:])
                long_type_dict[module_dot] = "module"

    module_list = []
    for item in long_type_dict.items():
        if item[1] == "module":
            module_list.append(item[0])

    for module in module_list:
        module_path = entry_path + '\\' + slash.join(module.split('.')) + ".py"

        gv_set = get_global_variables_in_a_py(module_path)
        for gv in gv_set:
            assert module + '.' + gv not in long_type_dict
            long_type_dict[module + '.' + gv] = "global_variable"

        func_set = get_func_in_a_py(module_path)
        for func in func_set:
            assert module + '.' + func not in long_type_dict
            long_type_dict[module + '.' + func] = "function"

        class_set = get_class_in_a_py(module_path)
        for cls in class_set:
            assert module + '.' + cls not in long_type_dict
            long_type_dict[module + '.' + cls] = "class"

        method_set = set()
        for cls in class_set:
            cls_method_set = get_all_methods_in_a_class(module_path, cls)
            method_set = method_set.union(cls_method_set)
        for method in method_set:
            assert module + '.' + method not in long_type_dict
            long_type_dict[module + '.' + method] = "method"

    NameUnit.long_type_dict = long_type_dict


def get_global_variables_in_a_py(py):
    res = set()

    import symtable

    content = ""
    with open(py, 'r') as file:
        content = file.read()

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []

    ident_list = list(table.get_identifiers())

    for ident in ident_list:
        if table.lookup(ident).is_imported() or table.lookup(ident).is_namespace():
            continue

        if table.lookup(ident).is_global() and table.lookup(ident).is_assigned():
            res.add(ident)

    return res


def get_func_in_a_py(py):
    import symtable

    content = ""
    with open(py, 'r') as file:
        content = file.read()

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []

    all_func_set = set()

    ident_list = list(table.get_identifiers())
    for ident in ident_list:
        if table.lookup(ident).is_namespace():
            func_or_class = table.lookup(ident).get_namespaces()
            if func_or_class[0].get_type() == 'function':
                all_func_set.add(ident)

    return all_func_set


def get_class_in_a_py(py):
    import symtable

    content = ""
    with open(py, 'r') as file:
        content = file.read()

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []
    all_class_set = set()

    ident_list = list(table.get_identifiers())
    for ident in ident_list:
        if table.lookup(ident).is_namespace():
            func_or_class = table.lookup(ident).get_namespaces()
            if func_or_class[0].get_type() == 'class':
                all_class_set.add(ident)

    return all_class_set


def get_special_func_in_a_py(py):
    import symtable

    content = ""
    try:
        with open(py, 'r',encoding = 'utf_8',errors='ignore') as file:
            content = file.read()
    except:
        try:
            with open(py, 'r', errors = 'ignore') as file:
                content = file.read()
        except:
            return set()

    try:
        table = symtable.symtable(content, "", compile_type="exec")
    except (SyntaxError, ValueError):
        nothing = set()
        return nothing

    all_func_set = set()

    ident_list = list(table.get_identifiers())
    for ident in ident_list:
        if table.lookup(ident).is_namespace():
            func_or_class = table.lookup(ident).get_namespaces()
            if func_or_class[0].get_type() == 'function':
                all_func_set.add(ident)

    simple_func_list, fstart, fend = get_a_pys_func_start_end_chart(py)
    simple_func_set = set(simple_func_list)

    special_func_set = all_func_set.difference(simple_func_set)
    return special_func_set


def get_special_class_in_a_py(py):
    import symtable

    content = ""
    try:
        with open(py, 'r',encoding = 'utf_8',errors='ignore') as file:
            content = file.read()
    except:
        try:
            with open(py, 'r',errors='ignore') as file:
                content = file.read()
        except:
            return []

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []

    all_class_set = set()

    ident_list = list(table.get_identifiers())
    for ident in ident_list:
        if table.lookup(ident).is_namespace():
            func_or_class = table.lookup(ident).get_namespaces()
            if func_or_class[0].get_type() == 'class':
                all_class_set.add(ident)

    simple_class_list, cstart, cend = get_a_pys_class_start_end_chart(py)
    simple_class_set = set(simple_class_list)

    special_class_set = all_class_set.difference(simple_class_set)
    return special_class_set


def get_special_method_in_a_py(py):
    import symtable

    content = ""
    try:
        with open(py, 'r',encoding = 'utf_8',errors='ignore') as file:
            content = file.read()
    except:
        try:
            with open(py, 'r',errors='ignore') as file:
                content = file.read()
        except:
            return []

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []

    all_method_set = set()

    ident_list = list(table.get_identifiers())
    for ident in ident_list:
        if table.lookup(ident).is_namespace():
            func_or_class = table.lookup(ident).get_namespaces()
            if func_or_class[0].get_type() == 'class':
                # assert len(func_or_class) == 1
                class_namespace = func_or_class[0]
                method_tuple = class_namespace.get_methods()
                for method in method_tuple:
                    all_method_set.add(ident + "." + method)

    simple_method_list, cfstart, cfend = get_a_pys_classinside_func_start_end_chart(py)
    simple_method_set = set(simple_method_list)

    special_method_set = all_method_set.difference(simple_method_set)
    return special_method_set


def get_all_methods_in_a_class(py, class_name):
    import symtable

    content = ""
    with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
        content = file.read()

    try:
        table = symtable.symtable(content, py, compile_type="exec")
    except (SyntaxError, ValueError):
        return []

    method_set = set()

    class_namespaces = table.lookup(class_name).get_namespaces()
    class_namespace = class_namespaces[0]
    method_tuple = class_namespace.get_methods()

    for method in method_tuple:
        method_set.add(class_name + "." + method)

    return method_set


def get_func_chart(content):
    fname1 = []
    fstart1 = []
    fend1 = []
    inside_a_func = False

    i = -1
    while i < len(content) - 1:
        i = i + 1
        #         print(i)
        line = content[i]
        if (inside_a_func == False):
            if (len(line) == 0):
                continue
            if (line[0:4] == 'def '):
                inside_a_func = True
                fstart1.append(i + 1)
                j = 3
                while (ord(line[j]) == 32):
                    j = j + 1
                start_idx = j
                while (ord(line[j]) != 40):
                    j = j + 1
                end_idx = j - 1
                tmp_name = line[start_idx:end_idx + 1]

                fname1.append(tmp_name)
                continue
        else:
            if (len(line) != 0 and ord(line[0]) != 32):
                tmp = i - 1
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                fend1.append(tmp + 1)
                i = i - 1
                inside_a_func = False
            elif (i == len(content) - 1 and (len(line) == 0 or ord(line[0]) == 32)):
                tmp = i
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                fend1.append(tmp + 1)

    return fname1, fstart1, fend1


def get_a_pys_func_start_end_chart(py):

    try:
        with open(py, 'r') as file:
            content = file.read().splitlines()
            fname, fstart, fend = get_func_chart(content)
    except:
        try:
            with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
                content = file.read().splitlines()
                fname, fstart, fend = get_func_chart(content)
        except:
            return [],[],[]

    return fname, fstart, fend


def get_a_pys_class_start_end_chart(py):
    content = []

    try:
        with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
            content = file.read().splitlines()
    except:
        try:
            with open(py, 'r') as file:
                content = file.read().splitlines()
        except:
            return [],[],[]

    cname = []
    cstart = []
    cend = []
    inside_a_class = False
    i = -1
    while i < len(content) - 1:
        i = i + 1
        line = content[i]
        if (inside_a_class == False):
            if (len(line) == 0):
                continue
            if (line[0:6] == 'class '):
                inside_a_class = True

                j = 5
                while (ord(line[j]) == 32):
                    j = j + 1
                start_idx = j

                found_fail = False
                while (ord(line[j]) != 40 and ord(line[j]) != 58):
                    j = j + 1
                    if j>=len(line):
                        found_fail = True
                        break
                if found_fail==True:
                    inside_a_class = False
                    continue
                end_idx = j - 1
                tmp_name = line[start_idx:end_idx + 1]

                cstart.append(i + 1)
                cname.append(tmp_name)
                continue
        else:
            if (len(line) != 0 and ord(line[0]) != 32):
                tmp = i - 1
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                cend.append(tmp + 1)
                i = i - 1
                inside_a_class = False
            elif (i == len(content) - 1 and (len(line) == 0 or ord(line[0]) == 32)):
                tmp = i
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                cend.append(tmp + 1)
                inside_a_class = False

    if inside_a_class==True:
        assert len(cstart)==len(cend)+1
        cend.append(cstart[-1])
    return cname, cstart, cend


def get_inside_class_func_chart(content, the_cname, the_cstart, the_cend):
    cfname = []
    cfstart = []
    cfend = []
    inside_a_cfunc = False
    i = the_cstart - 1 + 1
    while i < the_cend - 1:
        i = i + 1
        line = content[i]
        if (inside_a_cfunc == False):
            if (len(line) == 0):
                continue
            if (line[4:8] == 'def '):
                inside_a_cfunc = True
                cfstart.append(i + 1)
                j = 7
                while (ord(line[j]) == 32):
                    j = j + 1
                start_idx = j
                while (j<len(line) and ord(line[j]) != 40):
                    j = j + 1
                end_idx = j - 1
                tmp_name = line[start_idx:end_idx + 1]
                cfname.append(the_cname + r'.' + tmp_name)
                continue
        else:
            if (len(line) >= 5 and ord(line[4]) != 32):
                tmp = i - 1
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                cfend.append(tmp + 1)
                i = i - 1
                inside_a_cfunc = False
            elif (i == the_cend - 1 and (len(line) == 0 or re.match(r"[ ]*",line) or ord(line[4]) == 32)):
                tmp = i
                while (len(content[tmp]) == 0):
                    tmp = tmp - 1
                cfend.append(tmp + 1)

    if len(cfend)==len(cfstart)-1:
        cfend.append(the_cend)

    return cfname, cfstart, cfend


def get_a_pys_classinside_func_start_end_chart(py):
    cname, cstart, cend = get_a_pys_class_start_end_chart(py)
    if not (len(cname) == len(cstart) and len(cstart) == len(cend)):
        print(py)
        print(cname,"\n")
        print(cstart,"\n")
        print(cend,"\n")
    assert len(cname) == len(cstart) and len(cstart) == len(cend)
    cfname = []
    cfstart = []
    cfend = []
    try:
        with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
            content = file.read().splitlines()
            for i in range(len(cname)):
                cfnametmp, cfstarttmp, cfendtmp = get_inside_class_func_chart(content, cname[i], cstart[i], cend[i])
                if not (len(cfnametmp) == len(cfstarttmp) and len(cfstarttmp) == len(cfendtmp)):
                    print(py)
                    print(len(cfnametmp), len(cfstarttmp), len(cfendtmp))
                    print(cfnametmp, cfstarttmp, cfendtmp)
                    print(cname[i], cstart[i], cend[i])
                assert len(cfnametmp) == len(cfstarttmp) and len(cfstarttmp) == len(cfendtmp)
                cfname = cfname + cfnametmp
                cfstart = cfstart + cfstarttmp
                cfend = cfend + cfendtmp
    except:
        try:
            with open(py, 'r',errors='ignore') as file:
                content = file.read().splitlines()
                for i in range(len(cname)):
                    cfnametmp, cfstarttmp, cfendtmp = get_inside_class_func_chart(content, cname[i], cstart[i], cend[i])
                    if not (len(cfnametmp) == len(cfstarttmp) and len(cfstarttmp) == len(cfendtmp)):
                        print(py)
                        print(len(cfnametmp), len(cfstarttmp), len(cfendtmp))
                        print(cfnametmp, cfstarttmp, cfendtmp)
                        print(cname[i], cstart[i], cend[i])
                    assert len(cfnametmp) == len(cfstarttmp) and len(cfstarttmp) == len(cfendtmp)
                    cfname = cfname + cfnametmp
                    cfstart = cfstart + cfstarttmp
                    cfend = cfend + cfendtmp
        except:
            return [],[],[]

    return cfname, cfstart, cfend


def get_special_func_idx_set(py, special_func):
    def is_body(body_indentation, line):
        if (len(line) == 0):
            return True

        if (re.match(r"[ ]*$", line) != None):
            return True

        first_not_space = -1
        for i in range(len(line)):
            if (line[i] != ' '):
                first_not_space = i
                break
        if first_not_space < body_indentation:
            return False
        else:
            return True

    content = ""
    with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
        content = file.read().splitlines()

    res_idx_set = set()

    def_lineidx_indentation_dict = {}
    for i in range(len(content)):
        line = content[i]
        def_line = re.match(r"[ ]*def[ ]+" + special_func, line)
        if def_line:
            start_idx = line.find("def")
            def_lineidx_indentation_dict[i] = start_idx
            res_idx_set.add(i + 1)

    for def_idx in list(def_lineidx_indentation_dict.keys()):
        end_idx = len(content) - 1
        body_indentation = def_lineidx_indentation_dict[def_idx] + 4
        for i in range(def_idx + 1, len(content)):
            if (is_body(body_indentation, content[i])):
                continue
            else:
                end_idx = i - 1

                while (len(content[end_idx]) == 0):
                    end_idx = end_idx - 1

                for idx in range(def_idx + 1, end_idx + 1):
                    res_idx_set.add(idx + 1)
                break

    return res_idx_set



def get_special_class_idx_set(py, special_class):
    def is_body(body_indentation, line):

        if (len(line) == 0):
            return True

        if (re.match(r"[ ]*$", line) != None):
            return True

        first_not_space = -1
        for i in range(len(line)):
            if (line[i] != ' '):
                first_not_space = i
                break
        if first_not_space < body_indentation:
            return False
        else:
            return True

    content = ""
    with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
        content = file.read().splitlines()

    res_idx_set = set()


    def_lineidx_indentation_dict = {}
    for i in range(len(content)):
        line = content[i]
        def_line = re.match(r"[ ]*class[ ]+" + special_class, line)
        if def_line:
            start_idx = line.find("class")
            def_lineidx_indentation_dict[i] = start_idx
            res_idx_set.add(i + 1)

    for def_idx in list(def_lineidx_indentation_dict.keys()):
        end_idx = len(content) - 1
        body_indentation = def_lineidx_indentation_dict[def_idx] + 4
        for i in range(def_idx + 1, len(content)):
            if (is_body(body_indentation, content[i])):
                continue
            else:
                end_idx = i - 1

                while (len(content[end_idx]) == 0):
                    end_idx = end_idx - 1

                for idx in range(def_idx + 1, end_idx + 1):
                    res_idx_set.add(idx + 1)
                break


    return res_idx_set




def get_special_method_idx_set(py, special_method):
    def is_body(body_indentation, line):

        if (len(line) == 0):
            return True

        if (re.match(r"[ ]*$", line) != None):
            return True

        first_not_space = -1
        for i in range(len(line)):
            if (line[i] != ' '):
                first_not_space = i
                break
        if first_not_space < body_indentation:
            return False
        else:
            return True

    content = ""
    with open(py, 'r', encoding='UTF-8',errors='ignore') as file:
        content = file.read().splitlines()

    res_idx_set = set()

    class_method = special_method.split(".")
    class_name = class_method[0]
    method_name = class_method[1]

    cname, cstart, cend = get_a_pys_class_start_end_chart(py)
    if cname.count(class_name) == 0:
        lineno_idx_list = list(get_special_class_idx_set(py, class_name))
    else:
        assert cname.count(class_name) == 1
        idx = cname.index(class_name)
        class_start = cstart[idx]
        class_end = cend[idx]
        lineno_idx_list = range(class_start - 1, class_end)


    def_lineidx_indentation_dict = {}

    for i in lineno_idx_list:
        line = content[i]
        def_line = re.match(r"[ ]*def[ ]+" + method_name, line)
        if def_line:
            start_idx = line.find("def")
            def_lineidx_indentation_dict[i] = start_idx
            res_idx_set.add(i + 1)

    for def_idx in list(def_lineidx_indentation_dict.keys()):
        end_idx = len(content) - 1
        body_indentation = def_lineidx_indentation_dict[def_idx] + 4
        for i in range(def_idx + 1, len(content)):
            if (is_body(body_indentation, content[i])):
                continue
            else:
                end_idx = i - 1

                while (len(content[end_idx]) == 0):
                    end_idx = end_idx - 1

                for idx in range(def_idx + 1, end_idx + 1):
                    res_idx_set.add(idx + 1)
                break

    return res_idx_set

def get_diff(py1, py2):
    dl = difflib.Differ()
    with open(py1, 'r', encoding='UTF-8',errors='ignore') as file1:
        content1 = file1.read().splitlines()
    with open(py2, 'r', encoding='UTF-8',errors='ignore') as file2:
        content2 = file2.read().splitlines()
    diff_list = list(dl.compare(content1, content2))
    return diff_list

def get_left_right_idx_list(diff_list):
    lidx = 0
    ridx = 0
    l_list = []
    r_list = []
    for i in range(len(diff_list)):
        line = diff_list[i]
        if (len(line) == 0 or (line[0] != '+' and line[0] != '-' and line[0] != '?')):
            lidx = lidx + 1
            ridx = ridx + 1
        else:
            if line[0] == '?':
                pass
            else:
                if line[0] == '-':
                    lidx = lidx + 1
                    l_list.append(lidx)
                if line[0] == '+':
                    ridx = ridx + 1
                    r_list.append(ridx)

    return l_list, r_list

def get_mod_name(idx_list, fname_list, start_list, end_list):
    results = set()
    fnum = len(fname_list)
    for idx in idx_list:
        for i in range(fnum):
            if (idx >= start_list[i] and idx <= end_list[i]):
                results.add(fname_list[i])
                break
    return results

def get_func_change(py1, py2):
    add = set()
    sub = set()
    mod = set()

    fname1, fstart1, fend1 = get_a_pys_func_start_end_chart(py1)
    fname2, fstart2, fend2 = get_a_pys_func_start_end_chart(py2)

    cfname1, cfstart1, cfend1 = get_a_pys_classinside_func_start_end_chart(py1)
    cfname2, cfstart2, cfend2 = get_a_pys_classinside_func_start_end_chart(py2)

    fname1 = fname1 + cfname1
    fstart1 = fstart1 + cfstart1
    fend1 = fend1 + cfend1
    fname2 = fname2 + cfname2
    fstart2 = fstart2 + cfstart2
    fend2 = fend2 + cfend2

    diff_list = get_diff(py1, py2)
    l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)
    l_mod_f = get_mod_name(l_idx_list, fname1, fstart1, fend1)
    r_mod_f = get_mod_name(r_idx_list, fname2, fstart2, fend2)

    add = set(fname2).difference(set(fname1))
    sub = set(fname1).difference(set(fname2))
    mod = set.union(l_mod_f, r_mod_f).difference(add).difference(sub)

    return add, sub, mod


def get_class_change(py1, py2):
    add = set()
    sub = set()
    mod = set()


    cname1, cstart1, cend1 = get_a_pys_class_start_end_chart(py1)
    cname2, cstart2, cend2 = get_a_pys_class_start_end_chart(py2)

    diff_list = get_diff(py1, py2)
    l_idx_list, r_idx_list = get_left_right_idx_list(diff_list)
    l_mod_c = get_mod_name(l_idx_list, cname1, cstart1, cend1)
    r_mod_c = get_mod_name(r_idx_list, cname2, cstart2, cend2)

    add = set(cname2).difference(set(cname1))
    sub = set(cname1).difference(set(cname2))
    mod = set.union(l_mod_c, r_mod_c).difference(add).difference(sub)

    return add, sub, mod



def file_analysis(old_file_lines, six_quotes, hashtap):

    def only_comments_in_class(b,a):
        before_line_idx = a - 1
        find_meaningful_before_line = False
        before_indentation = -1
        while before_line_idx>=0:
            if before_line_idx not in hashtap and len(old_file_lines[before_line_idx])!=0:
                find_meaningful_before_line = True
                before_indentation = old_file_lines[before_line_idx].find("def")
                if before_indentation == -1:
                    before_indentation = old_file_lines[before_line_idx].find("class")
                break
            before_line_idx = before_line_idx - 1

        if not find_meaningful_before_line or before_indentation == -1:
            return False

        after_line_idx = b + 1
        find_meaningful_after_line = False
        after_indentation = -1
        while after_line_idx < len(old_file_lines):
            if after_line_idx not in hashtap and len(old_file_lines[after_line_idx]) != 0:
                find_meaningful_after_line = True
                after_indentation = old_file_lines[after_line_idx].find("def")
                if after_indentation == -1:
                    after_indentation = old_file_lines[after_line_idx].find("class")
                break
            after_line_idx = after_line_idx + 1

        if not find_meaningful_after_line or after_indentation == -1:
            return False

        if before_indentation <= after_indentation:
            return True
        else:
            return False

    i = -1
    # inside_three_quotation = False
    comments_start = False
    bad_start = False
    for line in old_file_lines:
        i = i+1
        ret_1 = re.match(r"#+", line)
        if ret_1:
            hashtap.append(i)
            continue

        if re.search(r"\"\"\"",line):
            ret_2_1 = re.match(r"[^\"]*\"\"\"[^\"]*\"\"\"", line)
            if ret_2_1:
                continue

            ret_2 = re.match(r"[ ]*\"\"\"", line)
            if ret_2 == None:
                ret_2 = re.match(r"[ ]*r\"\"\"", line)
            if ret_2:
                if comments_start == True:
                    assert bad_start == False
                    six_quotes.append(i)
                    comments_start = False
                else: # comments_start == False
                    if bad_start == False:
                        six_quotes.append(i)
                        comments_start = True
                    else:
                        bad_start = False
                continue

            if comments_start == True:
                assert bad_start == False
                six_quotes.append(i)
                comments_start = False
            else:
                if bad_start == True:
                    bad_start = False
                else:
                    bad_start = True


    while six_quotes != []:
        a = six_quotes.pop()

        try:
            b = six_quotes.pop()

        except:
            continue
            pass

        temp = b

        if only_comments_in_class(a,b):
            continue

        while temp <= a:
            hashtap.append(temp)
            temp += 1

    return hashtap


def delete_comments(file_name):

    try:
        f = open(file_name, "rb")
        old_file = f.read()
        f.close()
    except:
        print("cannot open" + file_name)
    else:

        old_file = old_file.decode("utf-8",errors='ignore')
        old_file_lines = old_file.splitlines()
        six_quotes, hashtap = list(), list()
        hashtap = file_analysis(old_file_lines, six_quotes, hashtap)

        try:

            comment_list = sorted(set(hashtap))
            comment_file = list()
            for i in comment_list:
                comment = old_file_lines[i]
                comment_file.append(comment)
            new_file_list = list(i for i in range(len(old_file_lines)))
            for i in comment_list:
                new_file_list.remove(i)
            new_file_lines = list()
            for i in new_file_list:
                temp = old_file_lines[i]
                new_file_lines.append(temp)

        except:
            print("no comments")
        else:
            file_name_pre = file_name[:-3]
            with open(file_name_pre + "(noComments).py", "wb") as f:
                for i in new_file_lines:
                    f.write(i.encode("utf-8"))
                    f.write("\r\n".encode("utf-8"))



def get_version_change(package_path_1, package_path_2):
    top = TwoPy()
    top.set_path(package_path_1, package_path_2)
    top.remove_redundant_comments_free_files()
    top.recursion_diff_path()
    top.get_only_file_sub_add_func()
    top.get_common_file_diff_func()
    top.get_change_class_and_cls_common()
    top.get_change_special_functions()
    top.get_change_special_methods()
    top.get_change_special_class_and_cls_common()

    change_names = set()
    for unit in TwoPy.change_unit_list:
        change_names.add(unit.full_name)

    top.clear_all()

    return change_names



