# bash-argparse: simple command line parsing for `bash` scripts

`bash-argparse` is a tool to parse your `bash` scripts command-line arguments.

## Features

* Specify command-line arguments from a signature
* Short and long options
* Positional and optional arguments
* Type checking
* Default values
* Only requires a standard python (>= 3.7) installation

### `bash-argparse` vs `getopt`?

* **Ease-of-use**: If you already know any typed programming language, `bash-argparse` may feel more intuitive, since the script signature resembles a normal function definition.
* **Type Safety**: Skip writing input validation by relying on `bash-argparse` checking the user's input against the type specification. 
* **Automatic**: Rely on `bash-argparse` deducing the program's name and short-options.

## Install

### Requirements

* Python 3.7 or above

### Installation steps

Install it from `pip`:

```bash
pip install bash-argparse
```

Or check the artifacts from the GitHub actions pipelines to download a nightly build. 

## Basic Usage

Here is a basic example:

```bash
#!/bin/bash
set -eou pipefail

# accepts 4 options passed to the script (through `$@`)
#   * a boolean flag --foo/-f, or --no-foo
#   * an integer option --bar <I>/-b<I>
#   * and a string option --fuz <S>/-F <S>
#   * --help or -h to print the automatic help message
eval $( python3 -m bash-argparse \
        --signature "bool foo; int bar; string Fuz" \
        --description "This program does many things." \
        -- "$@" )

# the variables are set by `eval`
echo $FOO $BAR $FUZ
```

* `bash program.sh` prints `false 0 `
* `bash program.sh --bar 4` prints `false 4 `
* `bash program.sh -f --bar 4` prints `true 4 `
* `bash program.sh -f --fuz 'hello'` prints `true 0 hello`

## Documentation

See the documentation in [the doc/ directory](./doc/index.md)

## License

This project is distributed under the MIT License. For more information see the [LICENSE](./LICENSE) file.
