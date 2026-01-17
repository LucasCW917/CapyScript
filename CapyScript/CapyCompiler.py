from pathlib import Path

CCVersion = "1.0.0"

# Console Manipulation
class Console:
    @staticmethod
    def write(text):
        print(text)

    @staticmethod
    def clear():
        print("\033c", end="")

# Command Mappings
CommandMap = {
    # Console Manipulation
    "console.write": Console.write,
    "console.clear": Console.clear
}


class CapyCompiler:
    def __init__(self, version):
        self.version = version

    def compile(self, source_file):
        if self.version == "1.0.0":
            CCVersion = self.version

            content = Path(source_file).read_text()
            for line in content.split("\n"):
                parts = line.split(" ", 1)
                command = parts[0]
                argument = parts[1] if len(parts) > 1 else ""

                if command in CommandMap:
                    CommandMap[command](argument)

                else:
                    raise Exception("Unknown command: " + command)


        else:
            raise Exception("Unsupported CapyCompiler version: " + self.version + ". Current version is %s." % CCVersion)

