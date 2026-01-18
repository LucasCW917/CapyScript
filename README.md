# CapyScript Language Overview

CapyScript is a command-oriented scripting language built around explicit operations and minimal syntax.
Programs are executed line-by-line, with each line typically representing a single command invocation.

The language favors clarity over cleverness and is designed to be easy to parse, extend, and embed.

CapyScript does not currently aim to compete with general-purpose languages.
It exists to make scripting, tooling, and rapid GUI or console utilities approachable and hackable.

## Execution Model

CapyScript is executed by the CapyScript compiler/runtime, implemented in Python.

At a high level:

A .capy file is read line-by-line.

Each line is tokenized into:

- a command

- an optional argument string

Commands are dispatched through a command map.

Arguments are passed to the command handler as raw strings.

Commands may:

- mutate internal state

- call Python-backed functions

- create or manipulate GUI elements

- read or write registers

There is no AST, optimizer, or bytecode stage at this time.
Execution is direct and imperative.

## Syntax Basics

Each line in CapyScript represents a command.

General form:

```
command arguments
```

Whitespace separates tokens.
Arguments are usually passed as a single string and parsed by the command itself.

## Variables and Registers

CapyScript uses registers rather than traditional variables, though multiletter variables arestill valid.

Registers are typically single identifiers and are assigned by commands.

Example:

```
time.time A
time.ctime A B
```

Here:

- A receives the current time value

- B receives a formatted string representation of A

Registers can be referenced using the `$` prefix:

```
io.print $B
```

## Importing Modules

Modules are imported using the base.import command.

```
base.import io
base.import time
```

Imported modules expose commands that can be invoked using dot notation.

## Standard Library Overview

The standard library is modular and implemented in Python.

Each module corresponds to a Python class inside the module directory.

- Console I/O (io)

Common commands include:

- printing text

- requesting user input

- basic console interaction

Example:

```
io.print Hello, world!
io.input Press Enter to continue...
```

- Time Utilities (time)

The time module provides basic access to timestamps and formatting.

Example:

```
time.time A
time.ctime A B
io.print $B
```

- GUI Module

CapyScript includes a GUI system built on top of CustomTkinter.

GUI elements are created, configured, and laid out through commands.
Widgets are referenced by name and stored internally.

The GUI system is imperative and stateful by design.

* Important constraint:

A single container must use only one geometry manager (pack, grid, or place).
Mixing layout managers within the same container will result in runtime errors.

## External Libraries

External libraries are implemented as Python modules.

Each library:

- lives in the module directory

- defines a class with the same name as the library

- exposes static methods as CapyScript commands

Arguments are always passed as a single string.

Example:

```
class example:
@staticmethod
def demo(args):
a, b = args.split(" ")
```

CapyScript does not enforce argument validation.
Libraries are responsible for parsing and error handling.

## Design Goals

CapyScript is guided by the following principles:

- Simplicity over completeness

- Explicit behavior over implicit magic

- Easy extensibility through Python

- Fast iteration and experimentation

- Clear failure modes

## Non-Goals

CapyScript does not currently aim to provide:

- High-performance computation

- Static typing

- Advanced compiler optimizations

- Memory safety guarantees

- Formal specification or standard

These may change over time, but they are not current priorities.

## Roadmap (Tentative)

Possible future directions include:

- Improved CLI stability

- Better error reporting and diagnostics

- A formal syntax reference

- Module documentation generation

- Safer argument parsing utilities

- Optional compile-time validation

- GUI layout linting

This roadmap is intentionally flexible.

## Project Status

CapyScript is experimental.

Breaking changes may occur without notice.
Documentation and tooling are evolving alongside the language.

Contributions, discussion, and experimentation are encouraged.