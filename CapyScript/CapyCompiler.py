from pathlib import Path
import re

import inspect
import sys

import customtkinter as ctk
import tkinter as tk

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


# capygui (native)
#
# This capygui helper exposes nearly all CTk widgets and common operations:
# - Widget types supported: CTk, CTkToplevel, CTkFrame, CTkLabel, CTkButton,
#   CTkCheckBox, CTkRadioButton, CTkSegmentedButton, CTkEntry, CTkTextbox,
#   CTkSlider, CTkProgressBar, CTkOptionMenu, CTkComboBox, CTkSwitch,
#   CTkScrollableFrame, CTkImage (via Image/configure).
#
# - Supports both legacy positional syntax and key=value arguments.
# - Supports named tkinter variables via `variable=` or `textvariable=` using Registers.
# - Exposes widget helpers: get, set, insert, delete, select, deselect, scroll_to,
#   add (child or segmented value), bind, focus, lift, lower, update.
# - Provides global CTk helpers: set_appearance, set_theme
#
# Layout note: widget creation does NOT perform any layout. Use capygui.pack/grid/place explicitly.
class capygui:
    apps = {}
    elements = {}
    vars = {}  # named tkinter variables

    # --- Helpers ---
    @staticmethod
    def _get_parent(name):
        return capygui.apps.get(name) or capygui.elements.get(name)

    @staticmethod
    def _parse_kwargs(tokens):
        """
        Accepts a list of tokens. Each token either a positional value
        or key=value. Returns (positional_list, kwargs_dict).
        Values are run through resolve_variables and simple type conversions.
        """
        pos = []
        kw = {}
        for token in tokens:
            if "=" in token:
                k, v = token.split("=", 1)
                v = resolve_variables(v, Registers)
                # booleans
                if isinstance(v, str) and v.lower() in ("true", "false"):
                    v = v.lower() == "true"
                else:
                    # try numeric conversion
                    if isinstance(v, str):
                        try:
                            if "." in v:
                                v = float(v)
                            else:
                                v = int(v)
                        except Exception:
                            # comma-separated to list
                            if "," in v:
                                v = [x for x in v.split(",")]
                kw[k] = v
            else:
                pos.append(resolve_variables(token, Registers))
        return pos, kw

    @staticmethod
    def _ensure_variable(var_name, var_type="string"):
        """
        Create or return a tkinter Variable stored in capygui.vars.
        var_type: 'int' or 'string'
        """
        if var_name in capygui.vars:
            return capygui.vars[var_name]
        if var_type == "int":
            v = tk.IntVar()
        else:
            v = tk.StringVar()
        capygui.vars[var_name] = v
        return v

    @staticmethod
    def _resolve_variable(name, parent, kind="string"):
        if not isinstance(name, str):
            return name  # already a tk.Variable

        if name in capygui.vars:
            return capygui.vars[name]

        if kind == "int":
            var = tk.IntVar(master=parent)
        else:
            var = tk.StringVar(master=parent)

        if name in Registers:
            try:
                var.set(Registers[name])
            except Exception:
                pass

        capygui.vars[name] = var
        return var


    # --- Global CTk settings ---
    @staticmethod
    def set_appearance(mode_name: str):
        # usage: capygui.set_appearance Dark
        mode = resolve_variables(mode_name, Registers)
        try:
            ctk.set_appearance_mode(mode)
        except Exception:
            pass

    @staticmethod
    def set_theme(theme_name: str):
        # usage: capygui.set_theme blue
        theme = resolve_variables(theme_name, Registers)
        try:
            ctk.set_default_color_theme(theme)
        except Exception:
            pass

    # --- Window / host ---
    @staticmethod
    def Window(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        # backward compatible: Window name geometry title...
        if len(pos) >= 2:
            name = pos[0]
            geo = pos[1]
            title = " ".join(pos[2:]) if len(pos) > 2 else kw.pop("title", "")
            app = ctk.CTk()
            if geo:
                try:
                    app.geometry(geo)
                except Exception:
                    pass
            if title:
                try:
                    app.title(title)
                except Exception:
                    pass
            if kw:
                try:
                    app.configure(**kw)
                except Exception:
                    pass
            capygui.apps[name] = app
            return
        # explicit kw style
        name = kw.pop("name", None)
        if not name:
            raise Exception("Window requires a name")
        app = ctk.CTk()
        if "geometry" in kw:
            try:
                app.geometry(kw.pop("geometry"))
            except Exception:
                pass
        if "title" in kw:
            try:
                app.title(kw.pop("title"))
            except Exception:
                pass
        if kw:
            try:
                app.configure(**kw)
            except Exception:
                pass
        capygui.apps[name] = app

    @staticmethod
    def host(name):
        parent = capygui.apps.get(name)
        if parent:
            parent.mainloop()

    # --- Elements creation (do NOT layout here) ---
    @staticmethod
    def TopLevel(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, geo = pos[0], pos[1], pos[2]
            title = " ".join(pos[3:]) if len(pos) > 3 else kw.pop("title", "")
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
            geo = kw.pop("geometry", None)
            title = kw.pop("title", "")
        parent = capygui._get_parent(parent_name)
        top_level = ctk.CTkToplevel(parent)
        if geo:
            try:
                top_level.geometry(geo)
            except Exception:
                pass
        if title:
            try:
                top_level.title(title)
            except Exception:
                pass
        if kw:
            try:
                top_level.configure(**kw)
            except Exception:
                pass
        capygui.elements[name] = top_level

    @staticmethod
    def Frame(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, geo = pos[0], pos[1], pos[2]
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
            geo = kw.pop("geometry", None)
        parent = capygui._get_parent(parent_name)
        config = kw.copy()
        frame = ctk.CTkFrame(parent, **config) if config else ctk.CTkFrame(parent)
        # DO NOT place the frame here; layout must be explicit via capygui.place/pack/grid
        capygui.elements[name] = frame

    @staticmethod
    def Label(args):
        tokens = args.split()
        pos, kw = capygui._parse_kwargs(tokens)

        parent_name, name = pos[0], pos[1]
        parent = capygui._get_parent(parent_name)

        if len(pos) > 2:
            kw.setdefault("text", " ".join(pos[2:]))

        label = ctk.CTkLabel(parent, **kw)
        capygui.elements[name] = label


    @staticmethod
    def Button(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, text = pos[0], pos[1], pos[2]
            command = " ".join(pos[3:]) if len(pos) > 3 else None
            kw.setdefault("text", text)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
            command = kw.pop("command", None)
        parent = capygui._get_parent(parent_name)
        def _make_command(cmd):
            if not cmd:
                return None
            def _inner():
                cmd = resolve_variables(cmd, Registers)
                parts = cmd.split(" ", 1)
                c = parts[0]
                a = parts[1] if len(parts) > 1 else ""
                if c in CommandMap:
                    try:
                        CommandMap[c](a)
                    except Exception:
                        pass
            return _inner
        if isinstance(command, str):
            kw["command"] = _make_command(command)
        btn = ctk.CTkButton(parent, **kw) if kw else ctk.CTkButton(parent)
        # do NOT layout here
        capygui.elements[name] = btn

    @staticmethod
    def CheckBox(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, text = pos[0], pos[1], " ".join(pos[2:])
            kw.setdefault("text", text)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "variable" in kw and isinstance(kw["variable"], str):
            kw["variable"] = capygui._ensure_variable(kw["variable"], var_type="int")
        parent = capygui._get_parent(parent_name)
        checkbox = ctk.CTkCheckBox(parent, **kw) if kw else ctk.CTkCheckBox(parent)
        capygui.elements[name] = checkbox

    @staticmethod
    def RadioButton(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, text = pos[0], pos[1], " ".join(pos[2:])
            kw.setdefault("text", text)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "variable" in kw and isinstance(kw["variable"], str):
            kw["variable"] = capygui._ensure_variable(kw["variable"], var_type="string")
        parent = capygui._get_parent(parent_name)
        radiobutton = ctk.CTkRadioButton(parent, **kw) if kw else ctk.CTkRadioButton(parent)
        capygui.elements[name] = radiobutton

    @staticmethod
    def SegmentedButton(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 2:
            parent_name, name = pos[0], pos[1]
            if len(pos) >= 3:
                kw.setdefault("values", pos[2].split(","))
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "variable" in kw and isinstance(kw["variable"], str):
            kw["variable"] = capygui._ensure_variable(kw["variable"], var_type="string")
        parent = capygui._get_parent(parent_name)
        segmented_button = ctk.CTkSegmentedButton(parent, **kw) if kw else ctk.CTkSegmentedButton(parent)
        capygui.elements[name] = segmented_button

    @staticmethod
    def Entry(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 2:
            parent_name, name = pos[0], pos[1]
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "textvariable" in kw and isinstance(kw["textvariable"], str):
            kw["textvariable"] = capygui._ensure_variable(kw["textvariable"], var_type="string")
        parent = capygui._get_parent(parent_name)
        entry = ctk.CTkEntry(parent, **kw) if kw else ctk.CTkEntry(parent)
        capygui.elements[name] = entry

    @staticmethod
    def TextBox(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 2:
            parent_name, name = pos[0], pos[1]
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        parent = capygui._get_parent(parent_name)
        textbox = ctk.CTkTextbox(parent, **kw) if kw else ctk.CTkTextbox(parent)
        capygui.elements[name] = textbox

    @staticmethod
    def Slider(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 4:
            parent_name, name, from_, to = pos[0], pos[1], float(pos[2]), float(pos[3])
            kw.setdefault("from_", from_)
            kw.setdefault("to", to)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "variable" in kw and isinstance(kw["variable"], str):
            kw["variable"] = capygui._ensure_variable(kw["variable"], var_type="int")
        parent = capygui._get_parent(parent_name)
        slider = ctk.CTkSlider(parent, **kw) if kw else ctk.CTkSlider(parent)
        capygui.elements[name] = slider

    @staticmethod
    def ProgressBar(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 2:
            parent_name, name = pos[0], pos[1]
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        parent = capygui._get_parent(parent_name)
        progressbar = ctk.CTkProgressBar(parent, **kw) if kw else ctk.CTkProgressBar(parent)
        capygui.elements[name] = progressbar

    @staticmethod
    def OptionMenu(args):
        tokens = args.split()
        pos, kw = capygui._parse_kwargs(tokens)

        parent_name, name = pos[0], pos[1]
        parent = capygui._get_parent(parent_name)

        if len(pos) > 2:
            kw.setdefault("values", pos[2].split(","))

        if "values" in kw and isinstance(kw["values"], str):
            kw["values"] = [v.strip() for v in kw["values"].split(",")]

        if "variable" in kw:
            kw["variable"] = capygui._resolve_variable(
                kw["variable"], parent, "string"
            )

        widget = ctk.CTkOptionMenu(parent, **kw)
        capygui.elements[name] = widget

    @staticmethod
    def ComboBox(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, options = pos[0], pos[1], pos[2].split(",")
            kw.setdefault("values", options)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        parent = capygui._get_parent(parent_name)
        combobox = ctk.CTkComboBox(parent, **kw) if kw else ctk.CTkComboBox(parent)
        capygui.elements[name] = combobox

    @staticmethod
    def Switch(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, text = pos[0], pos[1], " ".join(pos[2:])
            kw.setdefault("text", text)
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
        if "variable" in kw and isinstance(kw["variable"], str):
            kw["variable"] = capygui._ensure_variable(kw["variable"], var_type="int")
        parent = capygui._get_parent(parent_name)
        switch = ctk.CTkSwitch(parent, **kw) if kw else ctk.CTkSwitch(parent)
        capygui.elements[name] = switch

    @staticmethod
    def ScrollableFrame(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, geo = pos[0], pos[1], pos[2]
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
            geo = kw.pop("geometry", None)
        parent = capygui._get_parent(parent_name)
        sf = ctk.CTkScrollableFrame(parent, **kw) if kw else ctk.CTkScrollableFrame(parent)
        # DO NOT place/layout here even if geometry was provided
        capygui.elements[name] = sf

    @staticmethod
    def Image(args):
        tokens = args.split(" ")
        pos, kw = capygui._parse_kwargs(tokens)
        if len(pos) >= 3:
            parent_name, name, path = pos[0], pos[1], " ".join(pos[2:])
        else:
            parent_name = kw.pop("parent", None)
            name = kw.pop("name", None)
            path = kw.pop("path", None)
        parent = capygui._get_parent(parent_name)
        try:
            image = ctk.CTkImage(file=path)
            label = ctk.CTkLabel(parent, image=image)
            label._ctk_image = image
            # do NOT pack/place here
            capygui.elements[name] = label
        except Exception:
            # best-effort fallback: create empty label
            label = ctk.CTkLabel(parent, text="")
            capygui.elements[name] = label

    # --- Generic widget functions (pack/grid/place/configure/destroy) ---
    @staticmethod
    def pack(args):
        name, *rest = args.split()
        el = capygui.elements.get(name)
        if el:
            # rest tokens are parsed into kwargs (e.g. side=left, in=parentName etc.)
            pos, kw = capygui._parse_kwargs(rest)
            # support "in" or "in_" to refer to parent by name
            in_name = kw.pop("in", kw.pop("in_", None))
            if isinstance(in_name, str):
                in_parent = capygui._get_parent(in_name)
                if in_parent:
                    kw["in_"] = in_parent
            el.pack(**kw)

    @staticmethod
    def grid(args):
        parts = args.split(" ")
        element_name, row, column = parts[0], int(parts[1]), int(parts[2])
        options = {}
        if len(parts) > 3:
            _, kw = capygui._parse_kwargs(parts[3:])
            options = kw
        el = capygui.elements.get(element_name)
        if el:
            # support "in" or "in_" to refer to parent by name
            in_name = options.pop("in", options.pop("in_", None))
            if isinstance(in_name, str):
                in_parent = capygui._get_parent(in_name)
                if in_parent:
                    options["in_"] = in_parent
            try:
                el.grid(row=row, column=column, **options)
            except Exception:
                el.grid(row=row, column=column)

    @staticmethod
    def place(args):
        parts = args.split(" ")
        element_name, x, y = parts[0], int(parts[1]), int(parts[2])
        options = {}
        if len(parts) > 3:
            _, kw = capygui._parse_kwargs(parts[3:])
            options = kw
        el = capygui.elements.get(element_name)
        if el:
            in_name = options.pop("in", options.pop("in_", None))
            if isinstance(in_name, str):
                in_parent = capygui._get_parent(in_name)
                if in_parent:
                    options["in_"] = in_parent
            try:
                el.place(x=x, y=y, **options)
            except Exception:
                el.place(x=x, y=y)

    @staticmethod
    def configure(args):
        parts = args.split(" ")
        element_name = parts[0]
        config_args = parts[1:]
        el = capygui.elements.get(element_name)
        if not el:
            return
        _, kw = capygui._parse_kwargs(config_args)
        # coerce variables when specified as names
        for k, v in list(kw.items()):
            if k in ("variable", "textvariable") and isinstance(v, str):
                # treat as named tk variable
                kw[k] = capygui._ensure_variable(v, var_type="int" if k == "variable" else "string")
        try:
            el.configure(**kw)
            # special-case image update if string path provided
            if "image" in kw and isinstance(kw["image"], str):
                try:
                    el.configure(image=ctk.CTkImage(file=kw["image"]))
                except Exception:
                    pass
        except Exception:
            # last-resort: try ctk image
            if "image" in kw and isinstance(kw["image"], str):
                try:
                    el.configure(image=ctk.CTkImage(file=kw["image"]))
                except Exception:
                    pass

    @staticmethod
    def destroy(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if el:
            try:
                el.destroy()
            except Exception:
                pass
            del capygui.elements[name]

    # --- Widget-specific runtime helpers exposed to script ---
    @staticmethod
    def get(args):
        # get <element> <destRegister>
        parts = args.split(" ", 1)
        name = parts[0]
        dest = parts[1] if len(parts) > 1 else ""
        el = capygui.elements.get(name)
        val = ""
        if not el:
            Registers[dest] = ""
            return
        try:
            # many CTk widgets implement get()
            if hasattr(el, "get"):
                val = el.get()
            # Label-like
            elif hasattr(el, "cget"):
                try:
                    val = el.cget("text")
                except Exception:
                    # fall back to variable
                    var = getattr(el, "variable", None)
                    if var:
                        val = var.get()
            else:
                var = getattr(el, "variable", None)
                if var:
                    val = var.get()
        except Exception:
            try:
                var = getattr(el, "variable", None)
                if var:
                    val = var.get()
            except Exception:
                val = ""
        Registers[dest] = val

    @staticmethod
    def set(args):
        # set <element> <value>
        parts = args.split(" ", 1)
        name = parts[0]
        value = resolve_variables(parts[1], Registers) if len(parts) > 1 else ""
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            # preferred API
            if hasattr(el, "set"):
                el.set(value)
                return
            # entry-like
            if hasattr(el, "delete") and hasattr(el, "insert"):
                try:
                    el.delete(0, tk.END)
                    el.insert(0, value)
                    return
                except Exception:
                    pass
            # variable-backed widgets
            var = getattr(el, "variable", None)
            if var:
                try:
                    var.set(value)
                    return
                except Exception:
                    pass
            # label/button
            try:
                el.configure(text=value)
            except Exception:
                pass
        except Exception:
            try:
                el.configure(text=value)
            except Exception:
                pass

    @staticmethod
    def insert(args):
        # insert <element> <index> <text>
        parts = args.split(" ", 2)
        name = parts[0]
        index = parts[1]
        text = resolve_variables(parts[2], Registers) if len(parts) > 2 else ""
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            el.insert(index, text)
        except Exception:
            try:
                el.insert(int(index), text)
            except Exception:
                # for Text widget index can be 'end' or '1.0' etc.
                try:
                    el.insert(index, text)
                except Exception:
                    pass

    @staticmethod
    def delete(args):
        # delete <element> <start> <end>
        parts = args.split(" ", 2)
        name = parts[0]
        start = parts[1] if len(parts) > 1 else "0"
        end = parts[2] if len(parts) > 2 else tk.END
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            el.delete(start, end)
        except Exception:
            try:
                el.delete(int(start), int(end) if end != tk.END else end)
            except Exception:
                pass

    @staticmethod
    def select(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            if hasattr(el, "select"):
                el.select()
                return
        except Exception:
            pass
        var = getattr(el, "variable", None)
        if var:
            try:
                var.set(1)
            except Exception:
                pass

    @staticmethod
    def deselect(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            if hasattr(el, "deselect"):
                el.deselect()
                return
        except Exception:
            pass
        var = getattr(el, "variable", None)
        if var:
            try:
                var.set(0)
            except Exception:
                pass

    @staticmethod
    def scroll_to(args):
        # scroll_to <scrollable_name> <y>
        parts = args.split(" ", 1)
        name = parts[0]
        y = float(resolve_variables(parts[1], Registers)) if len(parts) > 1 else 0.0
        el = capygui.elements.get(name)
        if not el:
            return
        try:
            # CTkScrollableFrame delegates to underlying canvas
            el.yview_moveto(y)
        except Exception:
            try:
                el.scroll_to(y)
            except Exception:
                pass

    @staticmethod
    def add(args):
        # add <parent> <child_or_value>
        # - If parent is a container and child exists as element name, it will re-parent that widget into parent.
        # - If parent is a CTkSegmentedButton, and second argument is a literal value (not an element name), it will attempt to add that value.
        parts = args.split(" ", 1)
        parent_name = parts[0]
        child_token = parts[1] if len(parts) > 1 else ""
        parent = capygui.elements.get(parent_name) or capygui.apps.get(parent_name)
        # segmented add: if parent exists and is segmented button
        if isinstance(parent, ctk.CTkSegmentedButton):
            # child_token may be a comma-separated list or single value
            values = []
            if child_token:
                child_token = resolve_variables(child_token, Registers)
                if "," in child_token:
                    values = [x for x in child_token.split(",")]
                else:
                    values = [child_token]
            try:
                # try to extend values via configure
                current = []
                try:
                    current = parent.cget("values") or []
                except Exception:
                    try:
                        current = getattr(parent, "_values", []) or []
                    except Exception:
                        current = []
                new_vals = list(current) + values
                parent.configure(values=new_vals)
                return
            except Exception:
                pass
        # container re-parenting: find child element
        child = capygui.elements.get(child_token)
        if parent and child:
            try:
                child.pack(in_=parent)
                return
            except Exception:
                try:
                    child.place(in_=parent)
                    return
                except Exception:
                    try:
                        child.grid(in_=parent)
                        return
                    except Exception:
                        pass

    @staticmethod
    def bind(args):
        # bind <element> <event> <command>
        parts = args.split(" ", 2)
        name = parts[0]
        event = parts[1]
        cmd = parts[2] if len(parts) > 2 else ""
        el = capygui.elements.get(name)
        if not el:
            return
        def handler(event_obj=None):
            command_str = resolve_variables(cmd, Registers)
            parts = command_str.split(" ", 1)
            c = parts[0]
            a = parts[1] if len(parts) > 1 else ""
            if c in CommandMap:
                try:
                    CommandMap[c](a)
                except Exception:
                    pass
        try:
            el.bind(event, handler)
        except Exception:
            pass

    @staticmethod
    def focus(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if el:
            try:
                el.focus()
            except Exception:
                try:
                    el.focus_set()
                except Exception:
                    pass

    @staticmethod
    def lift(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if el:
            try:
                el.lift()
            except Exception:
                pass

    @staticmethod
    def lower(args):
        name = args.strip()
        el = capygui.elements.get(name)
        if el:
            try:
                el.lower()
            except Exception:
                pass

    @staticmethod
    def update(args):
        # update <element>  (or "update all")
        name = args.strip()
        if name == "all":
            # update all app windows
            for a in capygui.apps.values():
                try:
                    a.update()
                except Exception:
                    pass
            return
        el = capygui.elements.get(name) or capygui.apps.get(name)
        if el:
            try:
                el.update()
            except Exception:
                pass


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

    def direct_compile(self, code_string):
        for line in code_string.split(";"):
            command, arguements = line.strip().split(" ", 1)[0], line.strip().split(" ", 1)[1]
            CommandMap[command](arguements)

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

    if args[0] == "--drun":
        if len(args) < 2:
            print("error: --drun requires code")
            return
        code = " ".join(args[1:])
        CapyCompiler().direct_compile(code)
        return

    print(f"error: unknown command '{args[0]}'")
    print_usage()


def print_usage():
    print(
        r"""usage:
  capy --ver
  capy --run <file>
  capy --drun <command> <arguements>

commands:
  --ver        show version
  --run FILE   run a source file
  --drun "CODE"  run code directly
"""
    )


if __name__ == "__main__":
    if mode == "release":
        main()

    elif mode == "debug":
        CapyCompiler().compile()