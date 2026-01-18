# CapyScript
A programming language designed for simplicity and ease of use, inspired by capybaras and their cute naure, unlike this language which isn't cute in any way.

## Features
- Simple and intuitive syntax
- Easy to learn for beginners
- Lightweight and fast
- Cross-platform compatibility
- Extensive standard library, including modules for:
  - Console Manipulation
  - Time
  - GUI
- Also supports external libraries for extended functionality via Python!

## Installation
To install CapyScript, follow these steps:
1. CD to the 'CapyScript' folder.
2. Execute `python builder.py` for Windows or `python3 builder.py` for Linux/Mac.
3. Check for a `dist` folder containing the executable.

## Getting Started
To get started with CapyScript, create a new file with the `.capy` extension and write your first CapyScript program:
The below is an example script that may or may not work!
```
base.import io
base.import time

time.time A
time.ctime A B

io.print $B
io.input Press Enter to continue...
```

## External Library Creation/Importation

Creating your own CapyScript library is really easy! Just create a Python file containing a class with the same name as your library inside of the `module` folder. Inside that class, define methods that you want to expose to CapyScript. Each method should start with the decorator `@staticmethod`. Arguements in CapyScript will be passed as strings, so if require 3 arguements, split the string received and index them as such: `parameter1, parameter2, parameter3 = args[0], args[1], args[2]`.
Otherwise if you wish to import an existing Python library, you can create a wrapper class that exposes the desired functionality to CapyScript in the same way. Or, if you wish to import somebody elses library, download it and save it to the `module` folder.

## Contributing
Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, fork the repository and submit a pull request.

## CLI
The CLI is currently doodoo, so please for the love of god don't use it, or your head might get melted off!