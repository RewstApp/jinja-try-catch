from __future__ import annotations

import inspect
from typing import Any, Callable, List, Tuple

from jinja2 import nodes
from jinja2.async_utils import async_variant
from jinja2.ext import Extension
from jinja2.parser import Parser

__all__ = ['TryCatchExtension']


class TryCatchExtension(Extension):
    """Jinja2 try/catch extension.

    This extension exposes {% try %}{% endtry %} block, with an optional {% catch %}.
    If the body of the {% try %} block raises an exception, the body of the {% catch %}
    block is rendered instead (or, if no {% catch %} is defined, an empty string is returned).
    If the body of the {% try %} block does not raise an exception, the body of the {% try %}
    block is rendered.

    Example:

        {% try %}
            The thing: {{- i_do_not_exist_and_throw_an_error -}}
        {% catch -%}
            Error: {{ exception }}
        {% endtry %}

    Result:
        Error: 'i_do_not_exist_and_throw_an_error' is undefined

    """
    tags = {'try'}

    def parse(self, parser: Parser):
        lineno = next(parser.stream).lineno

        out_nodes: List[nodes.Node] = []
        try_catch_args: List[nodes.Expr] = []

        try_body = self._parse_statements_or_empty(parser, ('name:endtry', 'name:catch'))

        if parser.stream.skip_if('name:catch'):
            catch_body = self._parse_statements_or_empty(parser, ('name:endtry',))

            # If we have a catch block, we define a macro function that can be called
            # if an exception is raised.
            catch_macro = nodes.Macro(
                '_on_catch',
                [nodes.Name('exception', 'param')],
                [],
                catch_body,
            )
            out_nodes.append(catch_macro)
            try_catch_args.append(nodes.Name(catch_macro.name, 'load'))

        parser.stream.expect('name:endtry')

        body = [
            *out_nodes,
            nodes.CallBlock(
                self.call_method('_try_catch', try_catch_args, lineno=lineno),
                [],
                [],
                try_body,
            ),
        ]

        # Encase everything in an artificial scoping block, to avoid exposing
        # the catch macro after the {% endtry %} block.
        return nodes.Scope(body, lineno=lineno)

    def _sync_try_catch(
        self, catch_body: Callable[[Exception], Any] | None = None, *, caller: Callable
    ):
        try:
            return caller()
        except Exception as exception:
            if catch_body:
                return catch_body(exception)
            else:
                return ''

    @async_variant(_sync_try_catch)
    async def _try_catch(
        self, catch_body: Callable[[Exception], Any] | None = None, *, caller: Callable
    ):
        try:
            res = caller()
            if inspect.isawaitable(res):
                res = await res
            return res
        except Exception as exception:
            if catch_body:
                catch_res = catch_body(exception)
                if inspect.isawaitable(catch_res):
                    catch_res = await catch_res
                return catch_res
            else:
                return ''

    def _parse_statements_or_empty(
        self, parser: Parser, end_tokens: Tuple[str, ...]
    ) -> List[nodes.Node]:
        stmts = parser.parse_statements(end_tokens=end_tokens)
        if not stmts:
            stmts = [nodes.Output([nodes.TemplateData('')])]
        return stmts
