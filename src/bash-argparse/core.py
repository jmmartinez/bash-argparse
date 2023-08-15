from argparse import (
    ArgumentParser,
    Action,
    ArgumentTypeError,
    SUPPRESS,
    Namespace,
)
from sys import stderr
from pathlib import Path, PosixPath
from re import compile as re_compile

from os import getppid, access, X_OK

VARARGS_DEST = "ARGS"


class StderrHelpAction(Action):
    def __init__(
        self, option_strings, dest=SUPPRESS, default=SUPPRESS, help=None
    ):
        super(StderrHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

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
        raise RuntimeError(f'Unknown type "{signature}"')


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

class BooleanType:
    def __init__(self, factory, _):
        self._factory = factory

    def parse(self, string_value):
        string_value = string_value.lower()
        true_set = ("y", "yes", "t", "true", "on", "1")
        false_set = ("n", "no", "f", "false", "off", "0")
        for the_set, the_value in ((true_set, True), (false_set, False)):
            if string_value in the_set:
                return the_value
        raise RuntimeError(f'"{string_value}" not a valid bool value')

    def default(self):
        return False

    @staticmethod
    def register_bool(option):
        try:
            from argparse import BooleanOptionalAction

            return {"action": BooleanOptionalAction}
        except ImportError:
            if not option.default():
                return {"action": "store_true"}
            true_flag_name = option.get_flag_name()
            false_flag_name = f"no-{true_flag_name}"
            option.set_flag_name(false_flag_name)
            return {"action": "store_false"}


class EnumType:
    def __init__(self, factory, match):
        self._factory = factory
        self._enum = tuple(map(str.strip, match["types"].split(",")))

    def parse(self, string_value):
        if string_value not in self._enum:
            enum_list = ",".join(self._enum)
            raise RuntimeError(
                f'"{string_value}" not a valid enum value {{{enum_list}}}'
            )
        return string_value

    def default(self):
        return self._enum[0]

    @staticmethod
    def register_enum(option):
        def parse_type(s):
            return option._type.parse(s)

        return {
            "type": parse_type,
            "choices": option._type._enum,
        }

class PathType:
    def __init__(self, factory, _):
        self._factory = factory

    def parse(self, string_value):
        return Path(string_value).absolute()

    def default(self):
        return None

    @staticmethod
    def register_path(option):
        is_required = option.default() is None and not option.is_positional()
        # ughhhh! this is ugly: accessing the child parse through the option
        register = {"type": lambda v: option._type.parse(v) }
        if is_required:
            register["required"] = True
        return register

class OutputPathType(PathType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, string_value):
        value = super().parse(string_value)
        if value.exists():
            raise ArgumentTypeError(f"{value} cannot override path")
        return value

class InputPathType(PathType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, string_value):
        value = super().parse(string_value)
        if not value.exists():
            raise ArgumentTypeError(f"{value} path does not exist")
        return value

class ListType:
    def __init__(self, factory, _):
        self._factory = factory

    def parse(self, string_value):
        listlike = re_compile(r"\[(?P<elements>\S+)\]")
        is_listlike = listlike.fullmatch(string_value)
        if is_listlike:
            return is_listlike["elements"].split(",")
        return [string_value]

    def default(self):
        return []

    @staticmethod
    def register_list(option):
        return {"action": "append"}


def register_value(option):
    def parse_type(s):
        return option._type.parse(s)

    return {"type": parse_type}


for T, register_option in (
    (int, register_value),
    (float, register_value),
    (str, register_value),
):
    TypeFactory.register(
        TypeFactory(f"{T.__name__}", T, get_basic_type(T), register_option)
    )

TypeFactory.register(
    TypeFactory("list", list, ListType, ListType.register_list)
)
TypeFactory.register(
    TypeFactory("bool", bool, BooleanType, BooleanType.register_bool)
)
TypeFactory.register(
    TypeFactory(
        "unsigned",
        int,
        get_basic_type_with_constraint(int, check_unsigned),
        register_value,
    )
)
TypeFactory.register(
    TypeFactory("enum<(?P<types>.+)>", str, EnumType, EnumType.register_enum)
)
TypeFactory.register(
    TypeFactory(
        "input_path",
        Path,
        InputPathType,
        InputPathType.register_path,
    )
)
TypeFactory.register(
    TypeFactory(
        "output_path",
        Path,
        OutputPathType,
        OutputPathType.register_path,
    )
)


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

    def get_shell_name(self):
        return self._name.replace("-", "_").upper()

    def get_flag_name(self):
        return self._flag_name

    def set_flag_name(self, new_flag_name):
        self._flag_name = new_flag_name

    def is_positional(self):
        return self._decorator == "@"

    def is_required(self):
        return self._decorator == "^"

    def register_option(self, argument_parser, short_flags):
        params = self._type._factory.register_option(self)

        dest = self.get_shell_name()
        if dest == VARARGS_DEST:
            raise RuntimeError(
                f'Argument "{self._name}" clashes with varargs output.'
            )

        if self.is_positional():
            if self.default() != self._type.default():
                raise RuntimeError(
                    f"""Positional argument "{self._name}" is always required. """
                     """Do not assign a default value."""
                )
            flag = [self.get_shell_name()]
        else:
            flag = ["--" + self.get_flag_name()]
            params["dest"] = dest
            params["required"] = params.get("required", False) or self.is_required()
            short_flag = next((c for c in self._name if c.isalpha()), None)
            if short_flag and short_flag not in short_flags:
                flag.append(f"-{short_flag}")
                short_flags.add(short_flag)

        argument_parser.add_argument(*flag, default=self.default(), **params)


def build_parser_from_signature(
    prog: str, signature: str, desc: str
) -> ArgumentParser:
    parser = ArgumentParser(prog=prog, description=desc, add_help=False)
    parser.add_argument("-h", "--help", action=StderrHelpAction)

    type_re = r"(?P<type>[\w,<>-]+)"
    name_re = r"(?P<decorator>[@\^]?)(?P<name>[\w-]+)"
    default_value_re = r"(?P<default>\S+)"
    arg_desc_parser = re_compile(
        rf"^\s*{type_re}\s*{name_re}\s*(=\s*{default_value_re})?\s*$"
    )
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
            raise RuntimeError(f'Could not parse "{arg_desc}"')

        name = match["name"]
        type_name = match["type"]
        default = match["default"]
        decorator = match["decorator"]

        option_type = TypeFactory.get_type(type_name)
        option = Option(name, option_type, default, decorator)
        option.register_option(parser, short_flags)
    return parser


BASH_FORMATER = {
    int: str,
    float: str,
    bool: lambda b: str(b).lower(),
    str: lambda s: f'"{s}"',
    PosixPath: lambda s: f'"{s}"',
}


def format_bash_basic_value(value) -> str:
    try:
        return BASH_FORMATER[type(value)](value)
    except LookupError:
        raise RuntimeError(f"Cannot serialize type to variable {type(value)}")


def format_bash_list_value(the_list: list) -> str:
    return "( {} )".format(" ".join(map(format_bash_basic_value, the_list)))


def dump_bash_variables(prefix: str, bash_vars: Namespace) -> None:
    for var, value in bash_vars.__dict__.items():
        if type(value) is list:
            bash_value: str = format_bash_list_value(value)
            print(f"declare -a {prefix}{var}={bash_value};")
        else:
            bash_value: str = format_bash_basic_value(value)
            print(f"{prefix}{var}={bash_value};")
    return

OUTPUT_FORMATER = {
    "bash" : dump_bash_variables,
}

def is_bash_exec_path(executable):
    shells = ("bash", "sh", "zsh")
    if executable in shells:
        return True
    is_shell_path = Path(executable).name in shells 
    return  is_shell_path and access(executable, X_OK)

def get_default_program():
    default = "<script.sh>"

    parent_pid = getppid()
    with open(f"/proc/{parent_pid}/cmdline") as fd:
        parent_argv = fd.read().split("\x00")

    if not parent_argv or not is_bash_exec_path(parent_argv[0]):
        return default

    while True:
        parent_argv = parent_argv[1:]
        if not parent_argv:
            return default

        arg = parent_argv[0]
        if arg.startswith("-"):
            continue
        arg_as_path = Path(arg)
        maybe_script_name = arg_as_path.name
        is_script = arg_as_path.exists() and maybe_script_name.endswith(".sh")
        if is_script:
            return maybe_script_name
    return default

def get_default_shell():
    return "bash"

def main():
    try:
        this_parser = ArgumentParser(
            description="Parse command line arguments.",
            prog="bash-argparse"
        )
        this_parser.add_argument(
            "-s",
            "--signature",
            type=str,
            help="The function signature: (int foo, bool b, ...)",
            required=True,
        )
        this_parser.add_argument(
            "-p",
            "--program",
            default=get_default_program(),
            help="The name of the program or script",
        )
        this_parser.add_argument(
            "-f",
            "--format",
            default=get_default_shell(),
            help="The output format to be used",
            choices=OUTPUT_FORMATER.keys()
        )
        this_parser.add_argument(
            "-d",
            "--description",
            default="Help",
            help="The description of the program",
        )
        this_parser.add_argument(
            "--prefix", default="", help="Add a prefix to the variables"
        )
        this_parser.add_argument(
            "--help-on-empty",
            action="store_true",
            help="If not argument is passed, print help",
        )
        this_parser.add_argument(
            "shell_args",
            type=str,
            nargs="*",
            help="Arguments to forward to the shell script parser",
        )
        args = this_parser.parse_args()

        shell_parser = build_parser_from_signature(
            args.program, args.signature, args.description
        )
        if args.help_on_empty and not args.shell_args:
            args.shell_args = ["--help"]
        shell_args = shell_parser.parse_args(args.shell_args)
        OUTPUT_FORMATER[args.format](args.prefix, shell_args)
    except (RuntimeError, ArgumentTypeError) as e:
        print(f"error: {e}", file=stderr)
        exit(-1)
