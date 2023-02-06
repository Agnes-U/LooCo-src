import os
import json
from entrance_extraction.main import get_all_used_api
from cg_generator.engine import main as cfmain
from cg_generator.engine import glo_add_package_name, ShareData
from utils.package_version_change import get_version_change
from utils.req import get_packname_and_cons, get_packname_and_cons_from_setup
import platform
import sys


if (platform.system() == 'Windows'):
    slash = "\\"
else:
    slash = r"/"

ospardir = os.path.abspath(os.pardir)
versionMapping = os.path.join(os.pardir, "libraries", "versionMapping.json")

def search_or_get_version_change(pack_name, known_version, unknown_version, known_package_path, unknown_package_path):

    name_change_list = list(get_version_change(known_package_path, unknown_package_path))
    return name_change_list

def one_pass(pack_name, known_verison, unknown_version,known_package_path, unknown_package_path, name_extension, outside_pack_names):

    def find_setup_path(dir_path):
        """
        find setup.py path
        :param dir_path:
        :return: setpy.py path or None
        """
        setup_path = None
        for f in os.listdir(dir_path):
            full_f = os.path.join(dir_path, f)
            if full_f.endswith(r"\setup.py") or full_f.endswith(r"/setup.py"):
                setup_path = full_f
                break

        if setup_path == None:
            parent_dir_path = slash.join(dir_path.split(slash)[:-1])
            for f in os.listdir(parent_dir_path):
                full_f = os.path.join(parent_dir_path, f)
                if full_f.endswith(r"\setup.py") or full_f.endswith(r"/setup.py"):
                    setup_path = full_f
                    break

        return setup_path

    def find_requirements_path(dir_path):
        """
        find requirements.txt path
        :param dir_path:
        :return:
        """
        requirements_path = None

        for f in os.listdir(dir_path):
            full_f = os.path.join(dir_path, f)
            if full_f.endswith(r"\requirements.txt") or full_f.endswith(r"/requirements.txt"):
                requirements_path = full_f
                break


        if requirements_path == None:
            parent_dir_path = slash.join(dir_path.split(slash)[:-1])
            for f in os.listdir(parent_dir_path):
                full_f = os.path.join(parent_dir_path, f)
                if full_f.endswith(r"\requirements.txt") or full_f.endswith(r"/requirements.txt"):
                    requirements_path = full_f
                    break

        return requirements_path

    def check_requirements_or_setup():
        """
        compare dependencies in requirements.txt or setup.py

        :return: bool
        """

        known_req = find_requirements_path(known_package_path)
        unknown_req = find_requirements_path(unknown_package_path)
        if known_req != None:
            known_pack_and_cons = get_packname_and_cons(known_req)
            assert type(known_pack_and_cons) == list
        else:
            known_setup = find_setup_path(known_package_path)
            if known_setup != None:
                known_pack_and_cons = get_packname_and_cons_from_setup(known_setup)
            else:
                known_pack_and_cons = []

        if unknown_req != None:
            unknown_pack_and_cons = get_packname_and_cons(unknown_req)
            assert type(unknown_pack_and_cons) == list
        else:
            unknown_setup = find_setup_path(unknown_package_path)
            if unknown_setup != None:
                unknown_pack_and_cons = get_packname_and_cons_from_setup(unknown_setup)
            else:
                unknown_pack_and_cons = []

        assert (type(known_pack_and_cons) == list and type(unknown_pack_and_cons) == list)
        for outside_pack_name in outside_pack_names:
            its_known_cons, its_unknown_cons= "",""
            req_has_outsid_pack_name = False
            for pack_and_cons in known_pack_and_cons:
                if pack_and_cons[0] == outside_pack_name:
                    req_has_outsid_pack_name = True
                    if len(pack_and_cons)>1:
                        its_known_cons = pack_and_cons[1]
                    break
            for pack_and_cons in unknown_pack_and_cons:
                if pack_and_cons[0] == outside_pack_name:
                    req_has_outsid_pack_name = True
                    if len(pack_and_cons)>1:
                        its_unknown_cons = pack_and_cons[1]
                    break
            if its_known_cons != its_unknown_cons:

                return False
        return True

    name_change = search_or_get_version_change(pack_name, known_verison, unknown_version, known_package_path, unknown_package_path)


    name_extension = set(name_extension)

    if glo_add_package_name:
        tmp = set()
        for name in name_extension:
            tmp_name = ".".join(name.split(".")[1:])
            tmp.add(tmp_name)
        name_extension = tmp
    intersection_name = name_extension.intersection(name_change)

    if(len(intersection_name) == 0):
        can_use = check_requirements_or_setup()

    else:
        can_use = False

    name_change_res_dict = dict()
    name_change_res_dict["unknown_version"] = unknown_version
    name_change_res_dict["name_change"] = list(name_change)
    name_change_res_dict["intersection_name"] = list(intersection_name)
    name_change_res_dict["can_use"] = can_use

    return can_use, name_change_res_dict

def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.loads(f.read())

def known_version_process(project_path, pack_name, known_package_path, results_package_project_dir=None):

    def get_json_file(json_file_path):
        ls = ""
        for name in name_base:
            ls += name
            ls += ","

        f = open(json_file_path,"w")
        f.close()
        partc = [known_package_path, "--language", "py", "--output",json_file_path, "--entry-functions", ls]
        cfmain(sys_argv=partc, if_add_package_name = glo_add_package_name)



    name_base = get_all_used_api(project_path, pack_name)
    # print("name_base size: ", len(name_base))
    # print("name_base: ", name_base, "\n")

    if len(name_base)==0:
        return 0,0, None, None


    if results_package_project_dir==None:
        results_package_project_dir = "result"

    json_file_path = os.path.join(results_package_project_dir, r"tmp.json")
    outside_json_file_path = os.path.join(results_package_project_dir, r"tmp-outside.json")
    entry_json_file_path = os.path.join(results_package_project_dir, r"tmp-entry.json")
    get_json_file(json_file_path)


    cg_json_file = read_json(json_file_path)
    name_extension = set()
    for key in cg_json_file:
        name_extension.add(key)
        for value in cg_json_file[key]:
            name_extension.add(value)

    entry_json_file = read_json(entry_json_file_path)
    for i in entry_json_file:
        if i not in name_extension:
            name_extension.add(i)


    json_file = read_json(outside_json_file_path)
    outside_pack_name = set()
    for key in json_file:
        outside_pack_name.add(key)
    if r"<builtin>" in outside_pack_name:
        outside_pack_name.remove(r"<builtin>")

    name_base_size = len(name_base)
    entry_json_file = read_json(entry_json_file_path)
    name_base_found_size = len(entry_json_file)

    return name_base_size, name_base_found_size, name_extension, outside_pack_name

def main(project_path, the_version, pack_name, actual_pack_name, version_suffixpath_dict, version_list,results_package_project_dir=None):

    # print(project_path)
    assert os.path.exists(project_path)
    for version, suffix_path in version_suffixpath_dict.items():
        if not os.path.exists(suffix_path):
            pass
            # print(version, suffix_path)
        assert os.path.exists(suffix_path)
    # print(the_version, version_list)
    assert the_version in version_list
    assert the_version in version_suffixpath_dict

    known_package_path = version_suffixpath_dict[the_version]
    name_base_size, name_base_found_size, name_extension, outside_pack_name = known_version_process(project_path, actual_pack_name, known_package_path,results_package_project_dir)
    if name_extension==None:
        name_extension_num = 0
    else:
        name_extension_num = len(name_extension)
    if name_extension==None and outside_pack_name==None:
        # print("name base is empty")
        return name_base_size, name_base_found_size, ["-"], name_extension_num

    if len(name_extension)==0:
        return name_base_size, name_base_found_size,["-"], name_extension_num

    expend_versions = []

    the_version_index = version_list.index(the_version)

    name_change_json_content = []


    for i in range(len(version_list)):
        if i == the_version_index:
            continue
        unknown_version = version_list[i]
        unknown_package_path = version_suffixpath_dict[unknown_version]
        can_use, name_change_res_dict = one_pass(pack_name, the_version, unknown_version, known_package_path, unknown_package_path, name_extension,
                                                 outside_pack_name)
        name_change_json_content.append(name_change_res_dict)
        if can_use:
            # print("============can use new version", unknown_version, "\n")
            expend_versions.append(unknown_version)
        else:
            # print("============cannot use new version", unknown_version, "\n")
            pass

    # print(expend_versions)
    # print("expend version num:", len(expend_versions))
    return name_base_size, name_base_found_size, expend_versions, name_extension_num

def get_version_list(pack_name):
    with open(versionMapping,'r') as fh:
        content = fh.read()
    mapping_dict = json.loads(content)
    return list(mapping_dict[pack_name].keys())

def get_version_suffixpath_dict(pack_name):
    with open(versionMapping,'r') as fh:
        content = fh.read()
    mapping_dict = json.loads(content)
    version_suffixpath_dict = mapping_dict[pack_name]
    for v in version_suffixpath_dict.keys():
        path = version_suffixpath_dict[v]
        path = slash.join(path.split("/"))
        version_suffixpath_dict[v] = path
    return mapping_dict[pack_name]

if __name__ == '__main__':

    if not sys.version.startswith("3.8"):
        raise Exception("please use Python3.8.")

    # TweetTel
    project_path = sys.argv[1]
    if not os.path.exists(project_path):
        project_path = os.path.join("..", "projects", project_path)
    assert os.path.exists(project_path)

    # requests
    pack_name = sys.argv[2]

    # '2.27.1'
    base_version = sys.argv[3]

    # '2.27.0'
    if len(sys.argv)>=5:
        new_version = sys.argv[4]
        version_list = [base_version, new_version]
    else:
        version_list = get_version_list(pack_name)

    version_suffixpath_dict = get_version_suffixpath_dict(pack_name)


    name_base_size, name_base_found_size, expend_versions, name_extension_num = main(project_path, base_version,
                                                                                         pack_name, pack_name,
                                                                                         version_suffixpath_dict,
                                                                                         version_list)
    risky = []
    for v in version_list:
        if v!=base_version and v not in expend_versions:
            risky.append(v)

    print("base version: ", base_version)
    print("safe new versions:", ", ".join(expend_versions))
    print("risky new versions:", ", ".join(risky))