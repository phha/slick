import typing as t

from functools import singledispatchmethod

import click
import PySimpleGUI as sg

LAYOUT_ROW_T = t.Iterable[t.Type[sg.Element]]
HANDLER_RETURN_T = t.Callable[[click.Parameter], LAYOUT_ROW_T]


class _LayoutMaker:
    def __init__(self):
        self.type_handlers: t.Dict[t.Hashable, HANDLER_RETURN_T] = {}
        self.name_handlers: t.Dict[str, HANDLER_RETURN_T] = {}

    def __call__(self, param):
        handler = self.name_handlers.get(param.name)
        if not handler:
            handler = self.type_handlers.get(param.type, self._default_handler)
        return handler(param)

    def for_type(self, type: t.Any):
        def decorator(fn: HANDLER_RETURN_T):
            self.type_handlers[type] = fn
            return fn

        return decorator

    def for_name(self, name: str):
        def decorator(fn: HANDLER_RETURN_T):
            self.name_handlers[name] = fn
            return fn

        return decorator

    @staticmethod
    def _default_handler(param: click.Parameter) -> LAYOUT_ROW_T:
        return [label_for(param), input_for(param)]


make_layout = _LayoutMaker()


def get_param_name(param: click.Parameter) -> str:
    name = (
        param.human_readable_name
        if hasattr(param, "human_readable_name")
        else param.name
    )
    return name


def label_for(param: click.Parameter, **kwargs) -> sg.Text:
    tooltip = param.help if hasattr(param, "help") else None
    name = get_param_name(param)
    if not kwargs:
        kwargs = {"tooltip": tooltip}
    return sg.Text(f"{name}:", **kwargs)


def input_for(
    param: click.Parameter, element: t.Type[sg.Element] = sg.Input, **kwargs
) -> sg.Element:
    args = {
        "key": param.name,
        "metadata": param,
    }
    if hasattr(element, "default_text"):
        args["default_text"] = param.default
    elif hasattr(element, "default"):
        args["default"] = param.default
    args.update(kwargs)
    return element(**args)


@make_layout.for_type(click.types.BOOL)
def _(param: click.Parameter):
    default = param.default or False
    return [
        label_for(param),
        input_for(param, sg.Checkbox, default=default, text=""),
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
        self.layout.append(
            [
                sg.Multiline(write_only=True, reroute_stdout=True, key="-STDOUT_"),
                sg.Multiline(write_only=True, reroute_stderr=True, key="-STDERR-"),
            ]
        )
        self.window = sg.Window(command.name, self.layout)

    def _make_args(self) -> t.Optional[t.Sequence[str]]:
        """
        Return all parameters as they are supposed to be passed to
        the click command.
        """
        params = []
        opts = []
        for element in self.window.element_list():
            param = element.metadata
            if isinstance(param, click.Argument):
                value = element.get()
                params.append(str(value))
            elif isinstance(param, click.Option):
                value = element.get()
                opt = param.opts[0]
                if param.is_bool_flag:
                    secondary = param.secondary_opts[0]
                    opts.append(opt) if value else opts.append(secondary)
                elif param.is_flag and value:
                    opts.append(opt)
                else:
                    opts.append(opt)
                    opts.append(str(value))
        return opts + params

    def __call__(self):
        """
        Run the ui loop.
        """
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break
            elif event == "Run":
                args = self._make_args()
                self.command.main(args, standalone_mode=False)
                # sg.popup(args, title="Arguments")

        self.window.close()
