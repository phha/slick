import typing as t

from functools import singledispatchmethod

import click
import PySimpleGUI as sg


class LayoutMaker:
    def __init__(self):
        self.handlers: t.Dict = {}

    def __call__(self, param):
        name = (
            param.human_readable_name
            if hasattr(param, "human_readable_name")
            else param.name
        )
        tooltip = param.help if hasattr(param, "help") else None
        return self.handlers[param.type](param, name, tooltip)

    def for_type(self, type):
        def decorator(fn):
            self.handlers[type] = fn
            return fn

        return decorator


make_layout = LayoutMaker()


@make_layout.for_type(click.types.STRING)
@make_layout.for_type(click.types.INT)
@make_layout.for_type(click.types.FLOAT)
def _(param: click.Parameter, name: str, tooltip: t.Optional[str]):
    return [
        sg.Text(f"{name}:", tooltip=tooltip),
        sg.Input(default_text=param.default if param.default else ""),
    ]


@make_layout.for_type(click.types.BOOL)
def _(param: click.Parameter, name: str, tooltip: t.Optional[str]):
    return [
        sg.Text(f"{name}:", tooltip=tooltip),
        sg.Checkbox(
            text="",
            metadata=param.name,
            default=param.default if param.default is not None else False,
        ),
    ]


class guify:
    @singledispatchmethod
    def __init__(self, command):
        raise NotImplementedError("Cannot guify this.")

    @__init__.register
    def _(self, command: click.Command):
        self.command = command
        self.layout = [make_layout(p) for p in command.params]
        if command.__doc__:
            self.layout = [[sg.Frame(command.__doc__.strip(), layout=self.layout)]]
        self.layout.append([sg.Button("Run")])
        self.window = sg.Window(command.name, self.layout)

    def __call__(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break
            elif event == "Run":
                self.command.invoke()
        self.window.close()
