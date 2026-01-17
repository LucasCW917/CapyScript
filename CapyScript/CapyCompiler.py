from pathlib import Path

CCVersion = "1.0.0"

Registers = {}

# Console Manipulation
class io:
    @staticmethod
    def write(text):
        ProcessedText = text.split(" ")

        for word in ProcessedText:
            if word.startswith("$"):
                reg_name = word[1:]
                if reg_name in Registers:
                    print(Registers[reg_name], end=" ")
                else:
                    print(f"<undefined:{reg_name}>", end=" ")

            else:
                 print(word, end=" ")

    @staticmethod
    def clear():
        print("\033c", end="")

    @staticmethod
    def read(Register, *prompt):
        Registers[Register] = input(" ".join(prompt))
    

# Command Mappings
CommandMap = {
    # Console Manipulation
    "io.write": io.write,
    "io.clear": io.clear,
    "io.read": io.read,
    "io.input": io.read
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

