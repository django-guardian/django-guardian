import _ast
import os
import sys
from setuptools import Command
#from pyflakes.scripts import pyflakes as flakes


def check(filename):
    from pyflakes import reporter as mod_reporter
    from pyflakes.checker import Checker
    codeString = open(filename).read()
    reporter = mod_reporter._makeDefaultReporter()
    # First, compile into an AST and handle syntax errors.
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError:
        value = sys.exc_info()[1]
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            reporter.unexpectedError(filename, 'problem decoding source')
        else:
            reporter.syntaxError(filename, msg, lineno, offset, text)
        return 1
    except Exception:
        reporter.unexpectedError(filename, 'problem decoding source')
        return 1
    else:
        # Okay, it's syntactically valid.  Now check it.
        lines = codeString.splitlines()
        warnings = Checker(tree, filename)
        warnings.messages.sort(key=lambda m: m.lineno)
        real_messages = []
        for m in warnings.messages:
            line = lines[m.lineno - 1]
            if 'pyflakes:ignore' in line.rsplit('#', 1)[-1]:
                # ignore lines with pyflakes:ignore
                pass
            else:
                real_messages.append(m)
                reporter.flake(m)
        return len(real_messages)


class RunFlakesCommand(Command):
    """
    Runs pyflakes against guardian codebase.
    """
    description = "Check sources with pyflakes"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            import pyflakes  # pyflakes:ignore
        except ImportError:
            sys.stderr.write("No pyflakes installed!\n")
            sys.exit(-1)
        thisdir = os.path.dirname(__file__)
        guardiandir = os.path.join(thisdir, 'guardian')
        warns = 0
        # Define top-level directories
        for topdir, dirnames, filenames in os.walk(guardiandir):
            paths = (os.path.join(topdir, f)
                     for f in filenames if f .endswith('.py'))
            for path in paths:
                if path.endswith('tests/__init__.py'):
                    # ignore that module (it should only gather test cases with
                    # *)
                    continue
                warns += check(path)
        if warns > 0:
            sys.stderr.write(
                "ERROR: Finished with total %d warnings.\n" % warns)
            sys.exit(1)
        else:
            print("No problems found in source codes.")
