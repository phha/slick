import click
import PySimpleGUI as sg
import pytest as pt

from pytest_mock import MockerFixture
from slick.guify import guify, make_layout


def test_illegal_type():
    with pt.raises(NotImplementedError):
        guify("hello")


def test_make_widget_for_type(mocker: MockerFixture):
    # given
    param = mocker.MagicMock()
    param.got_called = False

    @make_layout.for_type(param.type)
    def maker(param, name, tooltip):
        param.got_called = True

    # when
    make_layout(param)

    # then
    assert param.got_called


def test_make_text_widget(mocker: MockerFixture):
    # given
    param = mocker.MagicMock(spec=click.Parameter)
    param.type = click.types.STRING
    param.name = "hello"
    param.default = "x"
    param.human_readable_name = "hello"

    # when
    label, input = make_layout(param)

    # then
    assert isinstance(label, sg.Text)
    assert label.DisplayText == "hello:"


def test_guify():
    @click.command()
    @click.argument("something", metavar="What to say")
    @click.option("--debug/nodebug", help="Extra debug output")
    @click.option("--number", type=int, default=4)
    def hello_world(something, debug, number):
        """
        Say Hello World
        """
        pass

    guified = guify(hello_world)
    guified()
