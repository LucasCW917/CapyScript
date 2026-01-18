from pathlib import Path
import re

import inspect
import sys

Registers = {}
ver = "1.0.1"
mode = "release"

# Variable resolution (modular)
_VAR_PATTERN = re.compile(r'\$(\w+)|\$\{([^}]+)\}')

def resolve_variables(text: str, registers: dict, undefined_fmt: str = "<undefined:{name}>") -> str:
    if not text:
        return text

    def _repl(match):
        name = match.group(1) or match.group(2)
        if name in registers:
            return str(registers[name])
        return undefined_fmt.format(name=name)

    return _VAR_PATTERN.sub(_repl, text)


def set_register_from_arg(arg: str):
    parts = arg.split(" ", 1)
    name = parts[0] if parts else ""
    value = parts[1] if len(parts) > 1 else ""
    # Resolve variables in the value so you can do nested references
    Registers[name] = resolve_variables(value, Registers)


# Console Manipulation
class io:
    @staticmethod
    def write(text: str):
        processed = resolve_variables(text, Registers)
        print(processed)

    @staticmethod
    def clear():
        print("\033c", end="")

    @staticmethod
    def read(arg: str):
        parts = arg.split(" ", 1)
        name = parts[0] if parts else ""
        prompt = parts[1] if len(parts) > 1 else ""
        Registers[name] = input(prompt)

    @staticmethod
    def local(arg: str):
        set_register_from_arg(arg)

# Math
class math:
    @staticmethod
    def add(args):
        args = args.split(" ")
        target1, target2, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(target1, Registers))
        val2 = float(resolve_variables(target2, Registers))
        Registers[dest] = val1 + val2

    @staticmethod
    def sub(args):
        args = args.split(" ")
        target1, target2, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(target1, Registers))
        val2 = float(resolve_variables(target2, Registers))
        Registers[dest] = val1 - val2

    @staticmethod
    def mul(args):
        args = args.split(" ")
        target1, target2, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(target1, Registers))
        val2 = float(resolve_variables(target2, Registers))
        Registers[dest] = val1 * val2

    @staticmethod
    def div(args):  
        args = args.split(" ")
        target1, target2, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(target1, Registers))
        val2 = float(resolve_variables(target2, Registers))
        if val2 == 0:
            Registers[dest] = 0

        Registers[dest] = val1 / val2

    @staticmethod
    def pow(args):
        args = args.split(" ")
        base_val, exponent, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(base_val, Registers))
        val2 = float(resolve_variables(exponent, Registers))
        Registers[dest] = val1 ** val2
        
    @staticmethod
    def sqrt(args):
        args = args.split(" ")
        value, dest = args[0], args[1]
        val = float(resolve_variables(value, Registers))
        Registers[dest] = val ** 0.5

    @staticmethod
    def mod(args):
        args = args.split(" ")
        target1, target2, dest = args[0], args[1], args[2]
        val1 = float(resolve_variables(target1, Registers))
        val2 = float(resolve_variables(target2, Registers))
        Registers[dest] = val1 % val2

    @staticmethod
    def pi(args):
        args = args.split(" ")
        dest, digits = args[0], int(args[1])
        from math import pi
        Registers[dest] = round(pi, int(digits))

import time as t

# Time
class time:
    @staticmethod
    def sleep(arg: str):
        seconds = float(resolve_variables(arg, Registers))
        t.sleep(seconds)

    @staticmethod
    def time(args):
        dest = args.split(" ")[0]
        Registers[dest] = int(t.time())

    @staticmethod
    def ctime(args):
        args = args.split(" ")
        dest = args[1]
        target = resolve_variables("$" + args[0], Registers)
        Registers[dest] = t.ctime(int(target))

    @staticmethod
    def localtime(args):
        dest = args.split(" ")[0]
        Registers[dest] = t.localtime()

# Base
class base:
    @staticmethod
    def importmod(name: str):
        if name in globals():
            target = globals()[name]
            if inspect.isclass(target):
                for method_name, method in inspect.getmembers(target, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue
                    CommandMap[f"{name}.{method_name}"] = method
                return

        try:
            module = __import__(f"modules.{name}", fromlist=[""])
        except ModuleNotFoundError:
            raise Exception(f"Module '{name}' not found in globals or modules")

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if inspect.isclass(attr):
                for method_name, method in inspect.getmembers(attr, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue
                    CommandMap[f"{attr_name}.{method_name}"] = method


# Command Mappings
CommandMap = {
    "base.import": base.importmod
}


class CapyCompiler:
    def __init__(self):
        pass

    def compile(self, source_file):
        if source_file.split(".")[-1] != "capy":
            raise Exception("Invalid file type: " + "." + source_file.split(".")[-1])

        content = Path(source_file).read_text()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(" ", 1)
            command = parts[0]
            argument = parts[1] if len(parts) > 1 else ""

            if command in CommandMap:
                CommandMap[command](argument)
            else:
                raise Exception("Unknown command: " + command)


VERSION = "0.1.0"

def main():
    args = sys.argv[1:]

    if not args:
        print_usage()
        return

    if args[0] == "--ver":
        print(f"capyscript {ver}")
        return

    if args[0] == "--run":
        if len(args) < 2:
            print("error: --run requires a file")
            return

        filename = args[1]
        CapyCompiler().compile(filename)
        return

    print(f"error: unknown command '{args[0]}'")
    print_usage()


def print_usage():
    print(
        """usage:
  capyscript --ver
  capyscript --run <file>

commands:
  --ver        show version
  --run FILE   run a source file
"""
    )


if __name__ == "__main__":
    if mode == "release":
        main()

    elif mode == "debug":
        CapyCompiler().compile(r"C:\Users\vince\source\repos\CapyScript\CapyScript\script.capy")
