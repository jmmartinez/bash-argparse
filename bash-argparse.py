from argparse import ArgumentParser, Action, SUPPRESS, Namespace 
from sys import stderr
from re import compile as re_compile

class StderrHelpAction(Action):
    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help=None):
        super(StderrHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help(file=stderr)
        parser.exit(-1)

class TypeFactory:
    _types = []
    def __init__(self, pattern, storage_type, concrete_type, register):
        self._pattern = re_compile(pattern)
        self._storage_type = storage_type
        self._concrete_type = concrete_type
        self._register = register

    def get_concrete_type(self, signature):
        match = self._pattern.fullmatch(signature)
        if not match:
            return None
        return self._concrete_type(self, match)

    def register_option(self, argument_parser, option):
        self._register(argument_parser, option)

    @staticmethod
    def register(TF):
        TypeFactory._types.append(TF)

    @staticmethod
    def get_type(signature):
        for TF in TypeFactory._types:
            T = TF.get_concrete_type(signature)
            if T:
                return T
        raise RuntimeError(f"Unknown type \"{signature}\"")

def get_basic_type(T):
    class BasicType:
        def __init__(self, factory, _):
            self._factory = factory
        def parse(self, string_value):
            return T(string_value)
        def default(self):
            return T()
    return BasicType

def get_basic_type_with_constraint(T, check_constraint):
    basic = get_basic_type(T)
    class ConstrainedType(basic):
        def __init__(self, factory, match):
            super().__init__(factory, match)
        def parse(self, string_value):
            return check_constraint(super().parse(string_value))
        def default(self):
            return check_constraint(super().default())
    return ConstrainedType

def check_unsigned(value):
    if value < 0:
        raise RuntimeError(f"{value} is not unsigned")
    return value

class EnumType:
    def __init__(self, factory, match):
        self._factory = factory
        self._enum = tuple(map(str.strip, match["types"].split(",")))

    def parse(self, string_value):
        if string_value not in self._enum:
            raise RuntimeError(f"{string_value} not a valid enum value (" + ", ".join(self._enum) + ")")
        return string_value

    def default(self):
        return self._enum[0]

def register_bool(parser, option):
    flag_name = option.get_flag_name()
    flag = f"--{flag_name}"
    no_flag = f"--no-{flag_name}"
    bash_name = option.get_bash_name()
    default = option.default()
    for flag, action in ((flag, "store_true"), (no_flag, "store_false")):
        parser.add_argument(flag, dest=bash_name, default=default, action=action)
    return

def register_list(parser, option):
    flag_name = option.get_flag_name()
    flag = f"--{flag_name}"
    bash_name = option.get_bash_name()
    default = option.default()
    parser.add_argument(flag, dest=bash_name, default=default, action='append')
    return

def register_value(parser, option):
    flag_name = option.get_flag_name()
    flag = f"--{flag_name}"
    bash_name = option.get_bash_name()
    default = option.default()
    parse_type = lambda s: option._type.parse(s)
    parser.add_argument(flag, dest=bash_name, default=default, type=parse_type, required=False)
    return

for T, register_option in ((bool, register_bool), (int, register_value), (float, register_value), (str, register_value), (list, register_list)):
    TypeFactory.register(TypeFactory(f"{T.__name__}", T, get_basic_type(T), register_option))
TypeFactory.register(TypeFactory("unsigned", int, get_basic_type_with_constraint(int, check_unsigned), register_value))
TypeFactory.register(TypeFactory("enum<(?P<types>.+)>", str, EnumType, register_value))

class Option:
    def __init__(self, name, T, maybe_default_value):
        self._name = name
        self._type = T
        if maybe_default_value:
            self._default = T.parse(maybe_default_value)
        else:
            self._default = T.default()
    
    def default(self):
        return self._default

    def get_bash_name(self):
        return self._name.replace("-", "_").upper()

    def get_flag_name(self):
        return self._name.replace("_", "-").lower()

    def register_option(self, argument_parser):
        self._type._factory.register_option(argument_parser, self)

def build_parser_from_signature(prog : str, signature: str, desc : str) -> ArgumentParser:
    parser = ArgumentParser(prog=prog, description=desc, add_help=False)
    parser.add_argument("-h", "--help", action=StderrHelpAction)

    arg_desc_parser = re_compile(r"^\s*(?P<type>(\w|,|<|>)+)\s*(?P<name>\w+)\s*(=\s*(?P<default>\w+))?\s*$")
    vararg_parser = re_compile(r"^\s*\.\s*\.\s*\.\s*$")

    arguments = signature.split(";")
    for arg_desc in arguments:
        # if vararg add everuthing to the ARGS variable
        if vararg_parser.fullmatch(arg_desc):
            parser.add_argument("ARGS", nargs="*")
            continue

        match = arg_desc_parser.fullmatch(arg_desc)
        if not match:
            raise RuntimeError(f"Could not parse \"{arg_desc}\"")

        name = match["name"]
        type_name = match["type"]
        default = match["default"]

        option_type = TypeFactory.get_type(type_name)
        option = Option(name, option_type, default)
        option.register_option(parser)
    return parser

BASH_FORMATER = {
    int : str,
    float : str,
    bool : lambda b: str(b).lower(),
    str: lambda s: f"\"{s}\"",
}

def format_bash_basic_value(value) -> str:
    return BASH_FORMATER[type(value)](value)

def format_bash_list_value(the_list: list) -> str:
    return "( {} )".format(" ".join(map(format_bash_basic_value, the_list)))

def dump_bash_variables(prefix: str, bash_vars : Namespace) -> None:
    for var, value in bash_vars.__dict__.items():
        if type(value) is list: 
            bash_value : str = format_bash_list_value(value) 
            print(f"declare -a {prefix}{var}={bash_value};")
        else:
            bash_value : str = format_bash_basic_value(value) 
            print(f"{prefix}{var}={bash_value};")
    return

if __name__ == "__main__":
    try:
        this_parser = ArgumentParser(description='Parse command line arguments.')
        this_parser.add_argument('-s', '--signature', type=str,
                                help='The function signature: (int foo, bool b, ...)', required=True)
        this_parser.add_argument('-p', '--program', default="<script.sh>",
                                help='The name of the program or script')
        this_parser.add_argument('-d', '--description', default="Help",
                                help="The description of the program")
        this_parser.add_argument('--prefix', default="",
                                help="Add a prefix to the variables")
        this_parser.add_argument('--help-on-empty', action='store_true',
                                help="If not argument is passed, print help")
        this_parser.add_argument("bash_args", type=str, nargs='*', help="Arguments to forward to the bash script parser")
        args = this_parser.parse_args()

        bash_parser = build_parser_from_signature(args.program, args.signature, args.description)
        if args.help_on_empty and not args.bash_args:
            args.bash_args = ["--help"]
        bash_args = bash_parser.parse_args(args.bash_args)
        dump_bash_variables(args.prefix, bash_args)
    except RuntimeError as e:
        print(f"Error: {e}", file=stderr)
        exit(-1)
