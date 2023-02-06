import sys
import os
import json
import ast
# import astunparse
from multiprocessing import Pool
from subprocess import run

from .util import get_path_by_extension
from .API_name_formating import get_API_calls, get_api_ref_id


# from util import get_path_by_extension
# from API_name_formating import  get_API_calls, get_api_ref_id

def get_tree(filename):
    def get_tree_with_feature_version(filename, feature_version=None):
        """
        Get the entire AST for this file

        :param filename str:
        :rtype: ast
        """
        try:
            with open(filename) as f:
                raw = f.read()
        except ValueError:
            with open(filename, encoding='UTF-8', errors='ignore') as f:
                raw = f.read()
        if feature_version == None:
            tree = ast.parse(raw)
        else:
            tree = ast.parse(raw, feature_version=feature_version)
        return tree

    def process_refactor_get_tree(filename):
        refactor_py = os.path.join("utils", "refactor.py")
        to_3_prefix = r"python " + refactor_py + " -w -n --no-diffs --add-suffix=3"
        py2_py = filename
        assert os.path.exists(py2_py)
        order_list = ["python", refactor_py, "-w", "-n", "--no-diffs", "--add-suffix=3"]
        order_list.append(py2_py)
        py3_py = py2_py + "3"

        try:
            # print(subprocess.Popen(order))
            # print(order_list)
            run(order_list)
            assert os.path.exists(py3_py)
            tree = get_tree_with_feature_version(py3_py, feature_version=(3, 4))
            os.remove(py3_py)
            return tree
        except AssertionError as ae:
            # print("Could not change %r to python3 (%r) Skipping...", filename, ae)
            raise SyntaxError
        except SyntaxError as se:
            if os.path.exists(py3_py):
                os.remove(py3_py)
            raise SyntaxError

    def get_tree_with_feature_version(filename, feature_version=None):
        """
        Get the entire AST for this file

        :param filename str:
        :rtype: ast
        """
        try:
            with open(filename) as f:
                raw = f.read()
        except ValueError:
            with open(filename, encoding='UTF-8', errors='ignore') as f:
                raw = f.read()
        if feature_version == None:
            tree = ast.parse(raw)
        else:
            tree = ast.parse(raw, feature_version=feature_version)
        return tree

    def process_refactor_get_tree(filename):
        refactor_py = os.path.join("utils", "refactor.py")
        to_3_prefix = r"python " + refactor_py + " -w -n --no-diffs --add-suffix=3"
        py2_py = filename
        assert os.path.exists(py2_py)
        order_list = ["python", refactor_py, "-w", "-n", "--no-diffs", "--add-suffix=3"]
        order_list.append(py2_py)
        py3_py = py2_py + "3"


        try:
            # print(subprocess.Popen(order))
            # print(order_list)
            run(order_list)
            assert os.path.exists(py3_py)
            tree = get_tree_with_feature_version(py3_py, feature_version=(3, 4))
            os.remove(py3_py)
            return tree
        except AssertionError as ae:
            # print("Could not change %r to python3 (%r) Skipping...", filename, ae)
            raise SyntaxError
        except SyntaxError as se:
            if os.path.exists(py3_py):
                os.remove(py3_py)
            raise SyntaxError

    try:
        tree = get_tree_with_feature_version(filename, feature_version=(3, 8))
        return tree
    except:
        try:
            tree = get_tree_with_feature_version(filename)  
            return tree
        except:
            try:
                tree = get_tree_with_feature_version(filename, feature_version=(3, 4))
                return tree
            except:
                try:
                    tree = process_refactor_get_tree(filename)
                    return tree
                except Exception as e:
                    raise e


def djoin(*tup):
    """
    Convenience method to join strings with dots
    :rtype: str
    """
    if len(tup) == 1 and isinstance(tup[0], list):
        return '.'.join(tup[0])

    notnone = list()
    for item in tup:
        if item != None:
            notnone.append(item)
    tup = notnone

    return '.'.join(tup)

def get_call_dot_str_from_func(func):
    """
    Given a python ast that represents a function call, clear and create our
    generic Call object. Some calls have no chance at resolution (e.g. array[2](param))
    so we return nothing instead.

    :param func ast:
    :rtype: Call|None
    """

    if type(func) == ast.Attribute:
        owner_token = []
        val = func.value
        while True:
            try:
                if hasattr(val, 'attr'):
                    owner_token.append(val.attr)
                else:
                    owner_token.append(val.id)
                # owner_token.append(getattr(val, 'attr', val.id))
            except AttributeError:
                pass
            val = getattr(val, 'value', None)
            if not val:
                break
        if owner_token:
            owner_token = djoin(*reversed(owner_token))
            token = func.attr
            return r".".join([owner_token, token])

    if type(func) == ast.Name:
        token = func.id
        return token

    if type(func) in (ast.Subscript, ast.Call):
        return None

    return None


def get_star_join_call(filename, pack_name):
    try:
        tree = get_tree(filename)
    except:
        return []
    has_from_pack_import_star = False
    pack_strs = set()
    for element in ast.walk(tree):
        if type(element) == ast.ImportFrom and type(element.module)==str and element.module.startswith(pack_name) and (
                len(element.module) == len(pack_name) or element.module[len(pack_name)] == r".") and type(
            element.names[0]) == ast.alias and element.names[0].name == r'*':
            has_from_pack_import_star = True
            pack_strs.add(element.module)

    res = []

    if has_from_pack_import_star:
        calls = set()
        for element in ast.walk(tree):
            if type(element) != ast.Call:
                continue
            call = get_call_dot_str_from_func(element.func)
            if call:
                calls.add(call)
        for pack_str in pack_strs:
            for call_str in calls:
                res.append(r".".join([pack_str, call_str]))
    return res

def get_star_join_call_from_tree(tree, pack_name):

    has_from_pack_import_star = False
    pack_strs = set()
    for element in ast.walk(tree):
        if type(element) == ast.ImportFrom and type(element.module)==str and element.module.startswith(pack_name) and (
                len(element.module) == len(pack_name) or element.module[len(pack_name)] == r".") and type(
            element.names[0]) == ast.alias and element.names[0].name == r'*':
            has_from_pack_import_star = True
            pack_strs.add(element.module)

    res = []

    if has_from_pack_import_star:
        calls = set()
        for element in ast.walk(tree):
            if type(element) != ast.Call:
                continue
            call = get_call_dot_str_from_func(element.func)
            if call:
                calls.add(call)
        for pack_str in pack_strs:
            for call_str in calls:
                res.append(r".".join([pack_str, call_str]))
    return res


def get_used_api_by_star(data_dir, package_name):
    """
    Supplement, from package_ Name (. blablabla) import *_ Name (. blablabla) spliced as name_ Base result
    :param data_dir:
    :param package_name:
    :return:
    """

    all_file_names = get_path_by_extension(data_dir)
    all_results = set()
    for filename in all_file_names:
        # print(filename)
        file_results = get_star_join_call(filename, package_name)
        for call in file_results:
            all_results.add(call)
    return all_results

def search_star_py_all_call(tree, package_name):
    all_results = set()
    file_results = get_star_join_call_from_tree(tree, package_name)
    for call in file_results:
        all_results.add(call)
    return all_results


def get_all_used_api(data_dir, package_name):
    all_result = set()



    all_file_names = get_path_by_extension(data_dir)
    # print(all_result)
    for filename in all_file_names:
        try:
            tree = get_tree(filename)
        except SyntaxError as se:
            # print("Could not decode %r. (%r) Skipping...", filename, se)
            continue

        # 1 normal call
        normal_dlocator_output = get_used_api(tree, package_name)
        all_result = all_result.union(normal_dlocator_output)

        # 2
        part2 = sup_api(tree, package_name)
        # print(filename)
        # print(part2)
        all_result = all_result.union(part2)
        # 3 from package(.blabla) import *
        part3 = search_star_py_all_call(tree, package_name)
        all_result = all_result.union(part3)

    return all_result

def get_used_api(tree, package_name):

    package_name=package_name+"."
    api_results=set()

    tmp_results = get_API_calls(tree)
    for tmp_result in tmp_results:
        if tmp_result.startswith(package_name):
            tmp  = tmp_result.split(':')
            name = tmp[0] # api name
            kws = tmp[1] # keywords
            api_results.add(name)

    # print(api_results)
    return api_results


def sup_api(tree, package_name):
    # print(astunparse.dump(tree))
    id2fullname = get_api_ref_id(tree)
    pack_id2fullname = dict()
    for key in id2fullname:
        value = id2fullname[key]
        if value.startswith(package_name) and (len(value)==len(package_name) or value[len(package_name)]==r"."):
            pack_id2fullname[key]=value
    # print(pack_id2fullname)
    all_result = set()

    def vis_before(element):
        if hasattr(element, "flag_vis"):
            return True
        else:
            return False

    def mark_vis_subtree(element):
        for child in ast.iter_child_nodes(element):
            child.flag_vis = 1
            mark_vis_subtree(child)

    for element in ast.walk(tree):
        if type(element) in [ast.ImportFrom,ast.Import,ast.Call]:
            mark_vis_subtree(element)
        elif type(element) == ast.Name:
            if not vis_before(element):
                if element.id in pack_id2fullname:
                    all_result.add(pack_id2fullname[element.id])
        elif type(element) == ast.Attribute:
            if not vis_before(element):
                mark_vis_subtree(element)

                all_attr_or_name = True
                whole_dot_str = element.attr
                while (type(element.value) != ast.Name):
                    if type(element.value) != ast.Attribute:
                        all_attr_or_name = False
                        break
                    assert type(element.value) == ast.Attribute
                    whole_dot_str = element.attr + "." + whole_dot_str
                    element = element.value
                if all_attr_or_name == False:
                    continue
                whole_dot_str = element.value.id + "." + whole_dot_str

                for id in pack_id2fullname:
                    if whole_dot_str.startswith(id) and (
                            len(whole_dot_str) == len(id) or whole_dot_str[len(id)] == r"."):
                        all_result.add(pack_id2fullname[id] + whole_dot_str[len(id):])
                        break

    return all_result


if __name__ == '__main__':
    s = get_all_used_api(r"","")
    print(s)
    print(len(s))