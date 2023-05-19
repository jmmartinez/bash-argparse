from argparse import ArgumentParser, Action, ArgumentTypeError, SUPPRESS, Namespace
from sys import stderr
from pathlib import Path, PosixPath
from re import compile as re_compile

VARARGS_DEST="ARGS"

class StderrHelpAction(Action):
    def __init__(self, option_strings, dest=SUPPRESS,
                 default=SUPPRESS, help=None):
        super(StderrHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest, default=default,
            nargs=0, help=help)

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

    def register_option(self, option):
        return self._register(option)

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
            return T(str(string_value))
        def default(self):
            return T()
    return BasicType

def get_basic_type_with_constraint(T, check_constraint, default=None):
    class ConstrainedType(get_basic_type(T)):
        def __init__(self, factory, match):
            super().__init__(factory, match)
        def parse(self, string_value):
            return check_constraint(super().parse(string_value))
        def default(self):
            default_value = default or super().default()
            return check_constraint(default_value)
    return ConstrainedType

def check_unsigned(value):
    if value < 0:
        raise ArgumentTypeError(f"{value} is not unsigned")
    return value

def check_input_path(value):
    if not value.exists():
        raise ArgumentTypeError(f"{value} path does not exist")
    return value.absolute()

def check_output_path(value):
    if value.exists():
        raise ArgumentTypeError(f"{value} cannot override path")
    return value.absolute()

class BooleanType:
    def __init__(self, factory, _):
        self._factory = factory

    def parse(self, string_value):
        string_value = string_value.lower()
        true_set = ('y', 'yes', 't', 'true', 'on', '1')
        false_set = ('n', 'no', 'f', 'false', 'off', '0')
        for the_set, the_value in ((true_set, True), (false_set, False)):
            if string_value in the_set:
                return the_value
        raise RuntimeError(f"\"{string_value}\" not a valid bool value")

    def default(self):
        return False

    @staticmethod
    def register_bool(option):
        try:
            from argparse import BooleanOptionalAction
            return { "action" : BooleanOptionalAction }
        except ImportError:
            if not option.default():
                return { "action" : "store_true"}
            true_flag_name = option.get_flag_name()
            false_flag_name = f"no-{true_flag_name}"
            option.set_flag_name(false_flag_name)
            return { "action" : "store_false"}

class EnumType:
    def __init__(self, factory, match):
        self._factory = factory
        self._enum = tuple(map(str.strip, match["types"].split(",")))

    def parse(self, string_value):
        if string_value not in self._enum:
            enum_list = ",".join(self._enum)
            raise RuntimeError(f"\"{string_value}\" not a valid enum value {{{enum_list}}}")
        return string_value

    def default(self):
        return self._enum[0]

    @staticmethod
    def register_enum(option):
        parse_type = lambda s: option._type.parse(s)
        return {
            "type" : parse_type,
            "choices" : option._type._enum, 
        }

def register_list(option):
    return { "action" : "append" }

def register_value(option):
    parse_type = lambda s : option._type.parse(s)
    return { "type" : parse_type }

for T, register_option in ((int, register_value), (float, register_value), (str, register_value), (list, register_list)):
    TypeFactory.register(TypeFactory(f"{T.__name__}", T, get_basic_type(T), register_option))
TypeFactory.register(TypeFactory("bool", bool , BooleanType, BooleanType.register_bool))
TypeFactory.register(TypeFactory("unsigned", int, get_basic_type_with_constraint(int, check_unsigned), register_value))
TypeFactory.register(TypeFactory("enum<(?P<types>.+)>", str, EnumType, EnumType.register_enum))
TypeFactory.register(TypeFactory("input_path", Path, get_basic_type_with_constraint(Path, check_input_path), register_value))
TypeFactory.register(TypeFactory("output_path", Path, get_basic_type_with_constraint(Path, check_output_path), register_value))

class Option:
    def __init__(self, name, T, maybe_default_value, decorator):
        self._name = name
        self._type = T
        if maybe_default_value:
            self._default = T.parse(maybe_default_value)
        else:
            self._default = T.default()
        self._decorator = decorator
        self._flag_name = self._name.replace("_", "-").lower()
    
    def default(self):
        return self._default

    def get_bash_name(self):
        return self._name.replace("-", "_").upper()

    def get_flag_name(self):
        return self._flag_name

    def set_flag_name(self, new_flag_name):
        self._flag_name = new_flag_name

    def is_positional(self):
        return self._decorator == "@"

    def is_required(self):
        return self._decorator == "!"

    def register_option(self, argument_parser, short_flags):
        params = self._type._factory.register_option(self)

        dest = self.get_bash_name()
        if dest == VARARGS_DEST:
            raise RuntimeError(f"Argument \"{self._name}\" clashes with varargs output.")

        if self.is_positional():
            flag = [self.get_bash_name()]
        else:
            flag = ["--" + self.get_flag_name()]
            params["dest"] = dest
            params["required"] = self.is_required()
            short_flag = next((c for c in self._name if c.isalpha()), None)
            if short_flag and short_flag not in short_flags:
                flag.append(f"-{short_flag}")
                short_flags.add(short_flag)

        argument_parser.add_argument(*flag, default=self.default(), **params)

def build_parser_from_signature(prog : str, signature: str, desc : str) -> ArgumentParser:
    parser = ArgumentParser(prog=prog, description=desc, add_help=False)
    parser.add_argument("-h", "--help", action=StderrHelpAction)

    arg_desc_parser = re_compile(r"^\s*(?P<type>[\w,<>]+)\s*(?P<decorator>[@!]?)(?P<name>[\w-]+)\s*(=\s*(?P<default>\S+))?\s*$")
    vararg_parser = re_compile(r"^\s*\.\s*\.\s*\.\s*$")

    arguments = signature.split(";")
    short_flags = set()
    for i, arg_desc in enumerate(arguments):
        # if vararg add everything to the ARGS variable
        if vararg_parser.fullmatch(arg_desc):
            is_last = i == len(arguments) - 1
            if not is_last:
                raise RuntimeError(f"'{arg_desc}' specifier goes at the end")
            parser.add_argument(VARARGS_DEST, nargs="*")
            continue

        match = arg_desc_parser.fullmatch(arg_desc)
        if not match:
            raise RuntimeError(f"Could not parse \"{arg_desc}\"")

        name = match["name"]
        type_name = match["type"]
        default = match["default"]
        decorator = match["decorator"]

        option_type = TypeFactory.get_type(type_name)
        option = Option(name, option_type, default, decorator)
        option.register_option(parser, short_flags)
    return parser

BASH_FORMATER = {
    int : str,
    float : str,
    bool : lambda b: str(b).lower(),
    str: lambda s: f"\"{s}\"",
    PosixPath: lambda s: f"\"{s}\"",
}

def format_bash_basic_value(value) -> str:
    try:
        return BASH_FORMATER[type(value)](value)
    except LookupError:
        raise RuntimeError(f"Cannot serialize type to variable {type(value)}")

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
        print(f"error: {e}", file=stderr)
        exit(-1)
