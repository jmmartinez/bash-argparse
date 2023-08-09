# `bash-argparse` documentation

## Usage

To use `bash-argparse` simply call the tool as follows:

```bash
eval $(python -m bash-argparse --signature "<SIGNATURE>" -- "${OPTIONS_TO_PARSE}")
```

Use the `--signature "<SIGNATURE>"` option to specify the options accepted by your script. You can read more about this option in [this section](#the---signature-option).

Additionally, this script accepts the following options:

* `--program <PROG>`: The name to be used as the program name. If nothing is specified, it will try to deduce it from the command line of the parent process.
* `--description <DESCRIPTION>`: Description of the program to be shown with the help.
* `--prefix <PREFIX>`: Append a custom prefix to the variable names. See [the output section](#bash-argparse-output) for more information.
* `--help-on-empty`: If no option is passed, print the help and exit. 

## The `--signature` option 

The `--signature` option accepts a list of option descriptors separated by `;`. An option descriptor takes the form of the triple:

```
<type> <modifier><name>
```

* The [type](#types) is used to validate the value passed by the user of the program.
* The [name](#name-mangling) is used to generate an option name and variable destination name.
* The [modifiers](#modifiers) are used to add special properties to the option: [@ it is positional](#positional) or [! if it is required](#required).

Additionally, the last option descriptor may be `...` (three dots) indicating that the script accepts an unbounded number of positional arguments (more about this in the [Vararg section](#vararg)).

For example:
* `--signature "bool lights; int speed"` accepts the options: `--lights`, `--no-lights` and `--speed <N>`.
* `--signature "list items"` accepts several occurrences of the `--items` option. The parser will append them in a list in the order in which they appear in the command line.

### Types

#### `bool`

A `true` or `false` switch.

```bash
--signature "bool lights"
```

The following options can be used:

* `--light/-l` sets `LIGHTS=true`
* `--no-light` sets `LIGHTS=false`

Notice that `--light=0/1/on/off/true/false` is not accepted.

With python versions < 3.8, the behavior is slightly degraded. The option generated depends on the default value of the switch.

* If the default value is `true`, only `--no-lights` is generated.
* If the default value is `false`, only `--lights` and its short version `-l` is generated.

The default value is `false`, but it can be set to `on/off/true/false/1/0`.

#### `int` and `unsigned`

A signed or unsigned integer value.

```bash
--signature "int count"
```

The following option can be used:

* `--count=1234` sets `COUNT=1234`, or the shorter `-c 1234`.
* `--count=-1234` sets `COUNT=-1234`. Negative values are rejected if `unsigned` is used).

The default value is `0`.

#### `string`

A string.

```bash
--signature "string name"
```

The following option can be used:

* `--name=Juan` sets `NAME="Juan"`.
* `--name "Juan Manuel"`  sets `NAME="Juan Manuel"`. 
* Similarly, the shorthand `-n` option alias. 

The default value is the empty string "".

#### `list`

A list of strings.

```bash
--signature "list items"
```

The following option can be used:

* `--items=sunglasses` sets `ITEMS=( "sunglasses" )`.
* `--items=sunglasses --items spoon` sets `ITEMS=( "sunglasses" "spoon" )`.
* `--items=sunglasses --items spoon -i boots` sets `ITEMS=( "sunglasses" "spoon" "boots" )`.
* `--items=sunglasses --items spoon -i boots -i 4` sets `ITEMS=( "sunglasses" "spoon" "boots" "4" )`.

Then, one can iterate over the list in bash as usual:

```bash
for item in ${ITEMS[@]} do
  echo "I've got $item in my backpack"
done
```

#### `enum`

An string option that can only take a value among a predefined set. 

```bash
--signature "enum<eat,sleep,work> what_to_do"
```

The following option can be used:

* `--what-to-do=sleep` sets `WHAT_TO_DO=sleep`.
* Options of `enum` type default to the first value among the options, in this case: `WHAT_TO_DO=eat`.

#### input_path and output_path

_These are in beta and not yet usable_

### Name mangling

`bash-argparse` harmonizes the names of the options, both, for the accepted options and for the output variables.

* When converting a name into an option: underscores `_` are converted into dashes `-`, and every character is converted to lowercase.
  For example, `int FoO_bAz` becomes the option `--foo-baz`.
* When converting a name into a shell variable: dashes `-` are converted into underscores `_`, every character is converted to uppercase.
  From our previous example, `int FoO_bAz` becomes the variable `FOO_BAZ`.

### Short options

`bash-argparse` tries to deduce short-options for every name. To do this, it uses the first letter (even in uppercase) of the name,
as long as there is no conflict with the previous names.

For example,
* for `int foo` it proposes `-f` as short option,
* for `int foo; int baz` it proposes `-f` and `-b` respectively;
* for `int foo; int Fiz` it proposes `-f` and `-F`;
* for `int foo; int fuz` it proposes `-f` that corresponds to `--foo`. For `fuz`, only the long option `--fuz` is available.

### Modifiers

#### Required `^`

When the special character `^` prefixes a name, the option is treated as required.
Required arguments must always be set by the user.

The signature `int a; int ^foo; int b` will accept `--a 4 --foo 5 --b 6`. In this case, `A=4`, `FOO=5` and `B=6`.
Notice that `--a 4 --b 6` would not be accepted as there is no parameter for `foo`.

#### Positional `@`

When the special character `@` prefixes a name, the option is treated as a positional arguments.
Positional arguments do not need a flag to be passed, and, similarly to required arguments, they must always be set by the user.

The signature `int a; int @foo; int b` will accept `--a 4 5 --b 6`. In this case, `A=4`, `FOO=5` and `B=6`.
Notice that `--a 4 --b 6` would not be accepted as there is no parameter for `foo`.

### Vararg `...`

When the last element in the signature is `...`, all the extra positional arguments are appended to the `ARGS` output variable.

For example, for the signature `int foo, ...`
* `--foo 4` sets the variables `FOO=4` and `ARGS=( )`
* `--foo 1 a b 6` sets the variables `FOO=1` and `ARGS=( "a" "b" "6" )`

## `bash-argparse` output

The output of `bash-argparse` is a small program that assigns values to variables.

For example, the command line below
```bash
python -m bash-argparse --signature "int option" -- "--option=4"
```

prints to the standard output:

```bash
OPTION=4
```

Then, to set the variables to their corresponding values we have to evaluate this program using `eval`.

The `--prefix` option can be used to add a prefix to the variable names.
If the `--prefix="ARG_"` option is used, the output would be:

```bash
ARG_OPTION=4
```
