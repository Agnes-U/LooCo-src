import abc
import os


TRUNK_COLOR = '#966F33'
LEAF_COLOR = '#6db33f'
EDGE_COLOR = "#cf142b"
NODE_COLOR = "#cccccc"

def _find_links_for_call(call, node_a, all_nodes):
    """
        Given a call that happened on a node (node_a), return the node
        that the call links to and the call itself if >1 node matched.

        :param call Call:
        :param node_a Node:
        :param all_nodes list[Node]:

        :returns: The node it links to and the call if >1 node matched.
        :rtype: (Node|None, Call|None)
        """
    assert type(call) == Call
    assert type(node_a) == Node
    assert type(all_nodes) == list

    if call.is_analyzed:
        return call.results, None

    call.is_analyzed = True
    all_vars = node_a.get_variables_with_priority(call.line_number)

    assert len(all_vars) >= 2 and  len(all_vars) <= 4

    third_pirty_vars=[]

    for var_list in all_vars:
        if len(var_list)==0:
            continue
        current_priority_results = []
        for var in var_list:
            var_match = call.matches_variable(var, all_nodes)
            if var_match:
                # Unknown modules (e.g. third party) we don't want to match)
                if var_match == OWNER_CONST.UNKNOWN_MODULE:
                    third_pirty_vars.append(var)
                    continue
                if type(var_match) == list:
                    for single_match in var_match:
                        assert isinstance(single_match, Node)
                        current_priority_results.append(single_match)
                else:
                    assert isinstance(var_match, Node)
                    current_priority_results.append(var_match)

        if len(current_priority_results)>0:
            call.results = current_priority_results
            return call.results, None

    if call.token in __builtins__ and call.owner_token == None:
        return [create_fake_node("<builtin>." + call.token)], None

    return None, call

def create_fake_node(name, may_third_party_class = False):
    name_from_root = name
    token = name
    calls = []
    variables = None
    parent = None
    fake_node = Node(name_from_root, token, calls, variables, parent)
    fake_node.flag.is_fake = True
    fake_node.flag.may_third_party_class = may_third_party_class
    return fake_node

def create_fake_group(name):
    name_from_root = name
    token = name
    group_type = "FILE"
    display_type = None
    fake_group = Group(name_from_root, token, group_type, display_type)
    fake_group.flag.is_fake = True
    return fake_group

class Namespace(dict):
    """
    Abstract constants class
    Constants can be accessed via .attribute or [key] and can be iterated over.
    """
    def __init__(self, *args, **kwargs):
        d = {k: k for k in args}
        d.update(dict(kwargs.items()))
        super().__init__(d)

    def __getattr__(self, item):
        return self[item]


OWNER_CONST = Namespace("UNKNOWN_VAR", "UNKNOWN_MODULE")
GROUP_TYPE = Namespace("FILE", "CLASS", "NAMESPACE")


def is_installed(executable_cmd):
    """
    Determine whether a command can be run or not

    :param list[str] individual_files:
    :rtype: str
    """
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, executable_cmd)
        if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
            return True
    return False


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


def flatten(list_of_lists):
    """
    Return a list from a list of lists
    :param list[list[Value]] list_of_lists:
    :rtype: list[Value]
    """
    return [el for sublist in list_of_lists for el in sublist]



def _resolve_str_variable(variable, file_groups):
    """
    String variables are when variable.points_to is a string
    This happens ONLY when we have imports that we delayed processing for

    This function looks through all files to see if any particular node matches
    the variable.points_to string

    :param Variable variable:
    :param list[Group] file_groups:
    :rtype: Node|Group|str
    """
    for file_group in file_groups:
        for node in file_group.all_nodes():
            if any(ot == variable.points_to for ot in node.import_tokens):
                return node
        for group in file_group.all_groups():
            if any(ot == variable.points_to for ot in group.import_tokens):
                return group
    return OWNER_CONST.UNKNOWN_MODULE


class BaseLanguage(abc.ABC):
    """
    Languages are individual implementations for different dynamic languages.
    This is the superclass of Python, Javascript, PHP, and Ruby.
    Every implementation must implement all of these methods.
    For more detail, see the individual implementations.
    Note that the 'Tree' type is generic and will be a different
    type for different languages. In Python, it is an ast.AST.
    """

    @staticmethod
    @abc.abstractmethod
    def assert_dependencies():
        """
        :rtype: None
        """

    @staticmethod
    @abc.abstractmethod
    def get_tree(filename, lang_params):
        """
        :param filename str:
        :rtype: Tree
        """

    @staticmethod
    @abc.abstractmethod
    def separate_namespaces(tree):
        """
        :param tree Tree:
        :rtype: (list[tree], list[tree], list[tree])
        """

    @staticmethod
    @abc.abstractmethod
    def make_nodes(tree, parent):
        """
        :param tree Tree:
        :param parent Group:
        :rtype: list[Node]
        """

    @staticmethod
    @abc.abstractmethod
    def make_root_node(lines, parent):
        """
        :param lines list[Tree]:
        :param parent Group:
        :rtype: Node
        """

    @staticmethod
    @abc.abstractmethod
    def make_class_group(tree, parent):
        """
        :param tree Tree:
        :param parent Group:
        :rtype: Group
        """


class Variable():
    """
    Variables represent named tokens that are accessible to their scope.
    They may either point to a string or, once resolved, a Group/Node.
    Not all variables can be resolved
    """
    def __init__(self, token, points_to, line_number=None):
        """
        :param str token:
        :param str|Call|Node|Group points_to: (str/Call is eventually resolved to Nodes|Groups)
        :param int|None line_number:
        """
        assert token
        assert points_to
        self.token = token
        self.points_to = points_to
        self.line_number = line_number

    def __repr__(self):
        return f"<Variable token={self.token} points_to={repr(self.points_to)}"

    def to_string(self):
        """
        For logging
        :rtype: str
        """
        if self.points_to and isinstance(self.points_to, (Group, Node)):
            return f'{self.token}->{self.points_to.token}'
        return f'{self.token}->{self.points_to}'


class Call():
    """
    Calls represent function call expressions.
    They can be an attribute call like
        object.do_something()
    Or a "naked" call like
        do_something()

    """
    def __init__(self, token, line_number=None, owner_token=None, definite_constructor=False, is_analyzed = False):
        self.token = token
        self.owner_token = owner_token
        self.line_number = line_number
        self.definite_constructor = definite_constructor
        self.is_analyzed = is_analyzed
        self.results = []
        self.master_node = None

    def __repr__(self):
        return f"<Call owner_token={self.owner_token} token={self.token}>"

    def to_string(self):
        """
        Returns a representation of this call to be printed by the engine
        in logging.
        :rtype: str
        """
        if self.owner_token:
            return f"{self.owner_token}.{self.token}()"
        return f"{self.token}()"

    def is_attr(self):
        """
        Attribute calls are like `a.do_something()` rather than `do_something()`
        :rtype: bool
        """
        return self.owner_token is not None

    def matches_variable(self, variable, all_nodes):
        """
        Check whether this variable is what the call is acting on.
        For example, if we had 'obj' from
            obj = Obj()
        as a variable and a call of
            obj.do_something()
        Those would match and we would return the "do_something" node from obj.

        :param variable Variable:
        :rtype: Node
        """

        if self.is_attr():
            if self.owner_token == variable.token:
                if hasattr(variable.points_to, 'flag') and variable.points_to.flag.is_fake:
                    fake_parent_node_name = variable.points_to.name_from_root
                    fake_node = create_fake_node(fake_parent_node_name + "." + self.token)
                    return fake_node
                for node in getattr(variable.points_to, 'nodes', []):
                    if self.token == node.token:
                        return node
                for inherit_nodes in getattr(variable.points_to, 'inherits', []):
                    for node in inherit_nodes:
                        if type(node)!=Node:
                            continue
                        if self.token == node.token:
                            return node
                for subgroup in getattr(variable.points_to, 'subgroups', []):
                    if self.token == subgroup.token and subgroup.get_constructor():
                        return subgroup.get_constructor()
                if variable.points_to in OWNER_CONST:
                    return variable.points_to

                if type(variable.points_to) == Call:
                    can_call = variable.points_to
                    if can_call.is_analyzed == False:
                        _find_links_for_call(can_call, can_call.master_node, all_nodes)
                    matched_node_list = []
                    for node in can_call.results:
                        if node.is_constructor:
                            cls = node.parent
                            assert type(cls)==Group and cls.group_type =="CLASS"
                            local_found=False
                            for method  in cls.nodes:
                                if self.token == method.token:
                                    matched_node_list.append(method)
                                    local_found = True
                            if local_found:
                                continue

                            for method_list in cls.inherits:
                                for method in method_list:
                                    if self.token == method.token:
                                        matched_node_list.append(method)

                        if node.flag.is_fake and node.flag.may_third_party_class :
                            class_name = node.name_from_root.split(".")[-1]
                            if(class_name[0]<'A' or class_name[0]>'Z'):
                                continue
                            prefix = node.name_from_root
                            suffix = self.token
                            matched_node_list.append(create_fake_node(prefix + "." + suffix))

                    if len(matched_node_list)>0:
                        return matched_node_list

            elif self.owner_token.startswith(variable.token+".") and hasattr(variable.points_to, 'flag') and variable.points_to.flag.is_fake:
                prefix = variable.points_to.name_from_root
                middle = self.owner_token[len(variable.token):]
                suffix = self.token
                return create_fake_node(prefix+middle+"."+suffix)

            # This section is specifically for resolving namespace variables
            if isinstance(variable.points_to, Group) \
               and variable.points_to.group_type == GROUP_TYPE.NAMESPACE:
                parts = self.owner_token.split('.')
                if len(parts) != 2:
                    return None
                if parts[0] != variable.token:
                    return None
                for node in variable.points_to.all_nodes():
                    if parts[1] == node.namespace_ownership() \
                       and self.token == node.token:
                        return node

            return None
        if self.token == variable.token:
            if isinstance(variable.points_to, Node):
                return variable.points_to
            if isinstance(variable.points_to, Group) \
               and variable.points_to.group_type == GROUP_TYPE.CLASS \
               and variable.points_to.get_constructor():
                return variable.points_to.get_constructor()

        return None


class ImportItem():
    def __init__(self,line_number, item, asname=None):
        self.line_number = line_number
        assert type(item) in (Node, Group)
        self.item = item
        self.asname = asname

class Flag():
    def __init__(self, import_done = False, calls_analyzed = False, is_fake = False, may_third_party_class =  False):
        self.import_done = import_done
        self.calls_analyzed = calls_analyzed
        self.is_fake = is_fake
        self.may_third_party_class = may_third_party_class


class Node():
    def __init__(self, name_from_root, token, calls, variables, parent, import_tokens=None,
                 line_number=None, is_constructor=False, is_analyzed=False):
        self.name_from_root = name_from_root
        self.token = token
        self.line_number = line_number
        self.calls = calls
        self.variables = variables
        self.import_tokens = import_tokens or []
        self.parent = parent
        self.is_constructor = is_constructor
        self.is_anayzed = is_analyzed
        self.flag = Flag()
        self.import_items = []

        self.uid = "node_" + os.urandom(4).hex()

        # Assume it is a leaf and a trunk. These are modified later
        self.is_leaf = True  # it calls nothing else
        self.is_trunk = True  # nothing calls it

    def __repr__(self):
        return f"<Node token={self.token} parent={self.parent}>"

    def name(self):
        """
        Names exist largely for unit tests
        :rtype: str
        """
        return f"{self.first_group().filename()}::{self.token_with_ownership()}"

    def first_group(self):
        """
        The first group that contains this node.
        :rtype: Group
        """
        parent = self.parent
        while not isinstance(parent, Group):
            parent = parent.parent
        return parent

    def file_group(self):
        """
        Get the file group that this node is in.
        :rtype: Group
        """
        parent = self.parent
        while parent.parent:
            parent = parent.parent
        return parent

    def is_attr(self):
        """
        Whether this node is attached to something besides the file
        :rtype: bool
        """
        return (self.parent
                and isinstance(self.parent, Group)
                and self.parent.group_type in (GROUP_TYPE.CLASS, GROUP_TYPE.NAMESPACE))

    def token_with_ownership(self):
        """
        Token which includes what group this is a part of
        :rtype: str
        """
        if self.is_attr():
            return djoin(self.parent.token, self.token)
        return self.token

    def namespace_ownership(self):
        """
        Get the ownership excluding namespace
        :rtype: str
        """
        parent = self.parent
        ret = []
        while parent and parent.group_type == GROUP_TYPE.CLASS:
            ret = [parent.token] + ret
            parent = parent.parent
        return djoin(ret)

    def label(self):
        """
        Labels are what you see on the graph
        :rtype: str
        """
        if self.line_number is not None:
            return f"{self.line_number}: {self.token}()"
        return f"{self.token}()"

    def remove_from_parent(self):
        """
        Remove this node from it's parent. This effectively deletes the node.
        :rtype: None
        """
        self.first_group().nodes = [n for n in self.first_group().nodes if n != self]

    def get_variables(self, line_number=None):
        """
        Get variables in-scope on the line number.
        This includes all local variables as-well-as outer-scope variables
        :rtype: list[Variable]
        """
        if line_number is None:
            ret = list(self.variables)
        else:
            ret = list([v for v in self.variables if v.line_number <= line_number])
        if any(v.line_number for v in ret):
            ret.sort(key=lambda v: v.line_number, reverse=True)

        parent = self.parent
        while parent:
            ret += parent.get_variables()
            parent = parent.parent
        return ret

    def get_variables_with_priority(self, line_number=None):
        """
            Get variables in-scope on the line number.
            This includes all local variables as-well-as outer-scope variables

            lower index has higher priority !!!
            :rtype: list[list[Variable], list[Variable]]
        """
        ans = []
        if line_number is None:
            ret = list(self.variables)
        else:
            ret = list([v for v in self.variables if v.line_number <= line_number])
        if any(v.line_number for v in ret):
            ret.sort(key=lambda v: v.line_number, reverse=True)
        ans.append(ret)

        parent = self.parent
        while parent:
            ret = []
            ret += parent.get_variables()
            ans.append(ret)
            parent = parent.parent
        return ans

    def modi_resolve_str_variable(self, variable):

        assert type(variable) == Variable

        can_import_items = []
        parent = self
        while parent:
            parent_import_items = parent.import_items
            parent = parent.parent
            for import_item in parent_import_items:
                can_import_items.append(import_item)

        for import_item in can_import_items:
            if import_item.asname == variable.token and import_item.line_number == variable.line_number: 
                return import_item.item

        return OWNER_CONST.UNKNOWN_MODULE

    def resolve_variables(self, file_groups):
        """
        For all variables, attempt to resolve the Node/Group on points_to.
        There is a good chance this will be unsuccessful.

        :param list[Group] file_groups:
        :rtype: None
        """
        for variable in self.variables:
            if isinstance(variable.points_to, str):
                # variable.points_to = _resolve_str_variable(variable, file_groups)
                variable.points_to = self.modi_resolve_str_variable(variable)

    def to_dot(self):
        """
        Output for graphviz (.dot) files
        :rtype: str
        """
        attributes = {
            'label': self.label(),
            'name': self.name(),
            'shape': "rect",
            'style': 'rounded,filled',
            'fillcolor': NODE_COLOR,
        }
        if self.is_trunk:
            attributes['fillcolor'] = TRUNK_COLOR
        elif self.is_leaf:
            attributes['fillcolor'] = LEAF_COLOR

        ret = self.uid + ' ['
        for k, v in attributes.items():
            ret += f'{k}="{v}" '
        ret += ']'
        return ret

    def to_dict(self):
        """
        Output for json files (json graph specification)
        :rtype: dict
        """
        return {
            'uid': self.uid,
            'label': self.label(),
            'name': self.name(),
        }


def _wrap_as_variables(sequence):
    """
    Given a list of either Nodes or Groups, wrap them in variables.
    This is used in the get_variables method to allow all defined
    functions and classes to be defined as variables
    :param list[Group|Node] sequence:
    :rtype: list[Variable]
    """
    return [Variable(el.token, el, el.line_number) for el in sequence]


class Edge():
    def __init__(self, node0, node1):
        self.node0 = node0
        self.node1 = node1

        # When we draw the edge, we know the calling function is definitely not a leaf...
        # and the called function is definitely not a trunk
        node0.is_leaf = False
        node1.is_trunk = False

    def __repr__(self):
        return f"<Edge {self.node0} -> {self.node1}"

    def to_dot(self):
        '''
        Returns string format for embedding in a dotfile. Example output:
        node_uid_a -> node_uid_b [color='#aaa' penwidth='2']
        :rtype: str
        '''
        ret = self.node0.uid + ' -> ' + self.node1.uid
        ret += f' [color="{EDGE_COLOR}" penwidth="2"]'
        return ret

    def to_dict(self):
        """
        :rtype: dict
        """
        return {
            'source': self.node0.uid,
            'target': self.node1.uid,
            'directed': True,
        }


class Group():
    """
    Groups represent namespaces (classes and modules/files)
    """
    def __init__(self, name_from_root, token, group_type, display_type, import_tokens=None,
                 line_number=None, parent=None, inherits=None,
                 file_absolute_path = None, global_variables = []):
        self.name_from_root = name_from_root
        self.token = token
        self.line_number = line_number
        self.nodes = []
        self.root_node = None
        self.subgroups = []
        self.parent = parent
        self.group_type = group_type
        self.display_type = display_type
        self.import_tokens = import_tokens or []
        self.inherits = inherits or []
        assert group_type in GROUP_TYPE
        self.file_absolute_path = file_absolute_path
        self.global_variables = global_variables
        self.flag = Flag()
        self.import_items = []


        self.uid = "cluster_" + os.urandom(4).hex()  # group doesn't work by syntax rules

    def __repr__(self):
        return f"<Group token={self.token} type={self.display_type}>"

    def label(self):
        """
        Labels are what you see on the graph
        :rtype: str
        """
        return f"{self.display_type}: {self.token}"

    def filename(self):
        """
        The ultimate filename of this group.
        :rtype: str
        """
        if self.group_type == GROUP_TYPE.FILE:
            return self.token
        return self.parent.filename()

    def add_subgroup(self, sg):
        """
        Subgroups are found after initialization. This is how they are added.
        :param sg Group:
        """
        self.subgroups.append(sg)

    def add_node(self, node, is_root=False):
        """
        Nodes are found after initialization. This is how they are added.
        :param node Node:
        :param is_root bool:
        """
        self.nodes.append(node)
        if is_root:
            self.root_node = node

    def all_nodes(self):
        """
        List of nodes that are part of this group + all subgroups
        :rtype: list[Node]
        """
        ret = list(self.nodes)
        for subgroup in self.subgroups:
            ret += subgroup.all_nodes()
        return ret

    def get_constructor(self):
        """
        Return the first constructor for this group - if any
        __init__ vs __new__
        :rtype: Node|None
        """
        assert self.group_type == GROUP_TYPE.CLASS
        constructors = [n for n in self.nodes if n.is_constructor]
        if constructors:
            return constructors[0]

        self.make_default_init()
        return self.get_constructor()

    def make_default_init(self):
        """
        add default initial method for a class

        :rtype: None
        """
        assert self.group_type == "CLASS"

        token = "__default_init__"
        name_from_root = self.name_from_root + '.' + token
        line_number = -1
        is_constructor = True
        import_tokens = []
        calls = []
        variables = []
        parent = self

        default_init_node = Node(name_from_root, token, calls, variables, parent, import_tokens=import_tokens,
                     line_number=line_number, is_constructor=is_constructor)

        call_to_super_init = Call(r"__init__")

        if type(self.inherits)==list and len(self.inherits)>=1 and type(self.inherits[0])==list: 
            all_possible_super_init = []
            for super_node_lsit in self.inherits:
                for super_node in super_node_lsit:
                    if not hasattr(super_node, "token"):
                        print("here")
                    if super_node.token=="__init__":
                        all_possible_super_init.append(super_node)
            call_to_super_init.results = all_possible_super_init
            call_to_super_init.is_analyzed = True

        call_to_super_init.master_node = default_init_node
        default_init_node.calls.append(call_to_super_init)

        self.add_node(default_init_node)

    def all_groups(self):
        """
        List of groups that are part of this group + all subgroups
        :rtype: list[Group]
        """
        ret = [self]
        for subgroup in self.subgroups:
            ret += subgroup.all_groups()
        return ret


    def get_variables(self, line_number=None):
        """
        Get in-scope variables from this group.
        This assumes every variable will be in-scope in nested functions
        line_number is included for compatibility with Node.get_variables but is not used

        :param int line_number:
        :rtype: list[Variable]
        """

        if self.root_node:
            variables = (self.root_node.variables
                         + _wrap_as_variables(self.subgroups)
                         + _wrap_as_variables(n for n in self.nodes if n != self.root_node))
            if any(v.line_number for v in variables):
                variables = sorted(variables, key=lambda v: v.line_number, reverse=True)
            return variables

        else:
            assert self.group_type == "CLASS"
            variables = []
            for node in self.nodes:
                method_variables = node.variables
                for v in method_variables:
                    if v.token!="self" and v.token.startswith("self"):
                        variables.append(v)
            return variables

    def remove_from_parent(self):
        """
        Remove this group from it's parent. This is effectively a deletion
        :rtype: None
        """
        if self.parent:
            self.parent.subgroups = [g for g in self.parent.subgroups if g != self]

    def to_dot(self):
        """
        Returns string format for embedding in a dotfile. Example output:
        subgraph group_uid_a {
            node_uid_b node_uid_c;
            label='class_name';
            ...
            subgraph group_uid_z {
                ...
            }
            ...
        }
        :rtype: str
        """

        ret = 'subgraph ' + self.uid + ' {\n'
        if self.nodes:
            ret += '    '
            ret += ' '.join(node.uid for node in self.nodes)
            ret += ';\n'
        attributes = {
            'label': self.label(),
            'name': self.token,
            'style': 'filled',
        }
        for k, v in attributes.items():
            ret += f'    {k}="{v}";\n'
        ret += '    graph[style=dotted];\n'
        for subgroup in self.subgroups:
            ret += '    ' + ('\n'.join('    ' + ln for ln in
                                       subgroup.to_dot().split('\n'))).strip() + '\n'
        ret += '};\n'
        return ret

class ShareFlag():
    analyzing_from_outside = True