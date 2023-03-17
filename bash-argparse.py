from argparse import ArgumentParser, Action, SUPPRESS, Namespace 
from sys import stderr

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

def is_vararg_marker(arg_desc : str) -> bool:
    return arg_desc.strip() == "..."

def is_on_off_switch(arg_default_value) -> bool:
    return type(arg_default_value) is bool and arg_default_value == bool()

def build_parser_from_signature(prog : str, signature: str, desc : str) -> ArgumentParser:
    parser = ArgumentParser(prog=prog, description=desc, add_help=False)
    parser.add_argument("-h", "--help", action=StderrHelpAction)

    arguments = signature.split(";")
    for arg_desc in arguments:
        if is_vararg_marker(arg_desc):
            parser.add_argument("ARGS", nargs="*")
            continue

        arg_ty_str, arg_name_init_str = arg_desc.split()
        arg_ty = eval(arg_ty_str)
        arg_default_value = arg_ty()

        if "=" in arg_name_init_str:
            arg_name, arg_default_value_str = arg_name_init_str.split("=")
            arg_default_value : arg_ty = eval(arg_default_value_str)
        else:
            arg_name = arg_name_init_str

        flag_name = "--" + arg_name.replace("_", "-")
        bash_var_name = arg_name.replace("-", "_").upper()
        if is_on_off_switch(arg_default_value):
            parser.add_argument(flag_name, dest=bash_var_name, default=arg_default_value, action='store_true')
        elif arg_ty is list:
            parser.add_argument(flag_name, dest=bash_var_name, default=arg_default_value, action='append')
        else:
            parser.add_argument(flag_name, dest=bash_var_name, default=arg_default_value, type=arg_ty, required=False)
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

def dump_bash_variables(bash_vars : Namespace) -> None:
    for var, value in bash_vars.__dict__.items():
        if type(value) is list: 
            bash_value : str = format_bash_list_value(value) 
            print(f"declare -a {var}={bash_value};")
        else:
            bash_value : str = format_bash_basic_value(value) 
            print(f"{var}={bash_value};")
    return

if __name__ == "__main__":
    this_parser = ArgumentParser(description='Parse command line arguments.')
    this_parser.add_argument('-s', '--signature', type=str,
                             help='The function signature: (int foo, bool b, ...)', required=True)
    this_parser.add_argument('-p', '--program', default="<script.sh>",
                             help='The name of the program or script')
    this_parser.add_argument('-d', '--description', default="Help",
                             help="The description of the program")
    this_parser.add_argument('--help-on-empty', action='store_true',
                             help="If not argument is passed, print help")
    this_parser.add_argument("bash_args", type=str, nargs='*', help="Arguments to forward to the bash script parser")
    args = this_parser.parse_args()

    bash_parser = build_parser_from_signature(args.program, args.signature, args.description)
    if args.help_on_empty and not args.bash_args:
        args.bash_args = ["--help"]
    bash_args = bash_parser.parse_args(args.bash_args)
    dump_bash_variables(bash_args)
