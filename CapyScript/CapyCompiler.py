from pathlib import Path
import re

import customtkinter

CCVersion = "1.0.0"

Registers = {}

# Variable resolution (modular)
_VAR_PATTERN = re.compile(r'\$(\w+)|\$\{([^}]+)\}')

def resolve_variables(text: str, registers: dict, undefined_fmt: str = "<undefined:{name}>") -> str:
    """
    Replace $name or ${name} occurrences in `text` using values from `registers`.
    Returns the resulting string; undefined registers use `undefined_fmt`.
    """
    if not text:
        return text

    def _repl(match):
        name = match.group(1) or match.group(2)
        if name in registers:
            return str(registers[name])
        return undefined_fmt.format(name=name)

    return _VAR_PATTERN.sub(_repl, text)


def set_register_from_arg(arg: str):
    """
    Parse an argument string of form "<name> <value...>" and set Registers[name] = resolved(value).
    If no value is provided, set to empty string.
    """
    parts = arg.split(" ", 1)
    name = parts[0] if parts else ""
    value = parts[1] if len(parts) > 1 else ""
    # Resolve variables in the value so you can do nested references
    Registers[name] = resolve_variables(value, Registers)


# Console Manipulation
class io:
    @staticmethod
    def write(text: str):
        # Expand variables and print (preserve trailing newline behavior like print)
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


# Command Mappings
CommandMap = {
    # Console Manipulation
    "io.write": io.write,
    "io.clear": io.clear,
    "io.read": io.read,
    "io.input": io.read,
    "io.local": io.local
}


class CapyCompiler:
    def __init__(self, version):
        self.version = version

    def compile(self, source_file):
        if self.version == "1.0.0":
            CCVersion = self.version

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

        else:
            raise Exception("Unsupported CapyCompiler version: " + self.version + ". Current version is %s." % CCVersion)

CapyCompiler(CCVersion).compile("script.capy")