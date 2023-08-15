from subprocess import Popen 
from sys import argv, stderr, stdout, stdin

with Popen(argv[1:], stdout=stdout, stderr=stderr, stdin=stdin) as proc:
    exit_code = proc.wait()
    exit_code = 1 if exit_code == 0 else 0
    stdout.flush()
    exit(exit_code)
