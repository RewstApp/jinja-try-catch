from typing import Any, Callable

import jinja2
import jinja2.ext
import jinja2.nativetypes
import pytest

from jinja_try_catch.extension import TryCatchExtension


@pytest.fixture
def env_kwargs() -> dict[str, Any]:
    return dict(
        extensions=[
            TryCatchExtension,
            jinja2.ext.ExprStmtExtension,
        ],
        undefined=jinja2.StrictUndefined,
    )


@pytest.fixture(params=[
    pytest.param(False, id='normal'),
    pytest.param(True, id='native'),
])
def is_native_env(request) -> bool:
    return request.param


@pytest.fixture
def env_class(is_native_env) -> type[jinja2.Environment]:
    return jinja2.nativetypes.NativeEnvironment if is_native_env else jinja2.Environment


@pytest.fixture
def preprocess_expected(is_native_env) -> Callable[[Any], Any]:
    return (lambda o: o) if is_native_env else str


@pytest.fixture
def sync_env(env_kwargs, env_class) -> jinja2.Environment:
    return env_class(**env_kwargs)


@pytest.fixture
def async_env(env_kwargs, env_class) -> jinja2.Environment:
    return env_class(**env_kwargs, enable_async=True)


TEST_CASES = {
    'try-no_catch-no_error': (
        # language=jinja2
        '''
        {%- try -%}
            try
        {%- endtry -%}
        ''',
        'try',
    ),
    'try_empty-no_catch-no_error': (
        # language=jinja2
        '''
        {%- try -%}
        {%- endtry -%}
        '''.strip(),
        '',
    ),
    'none-no_catch-no_error': (
        # language=jinja2
        '''
        {%- try -%}
            {{ None }}
        {%- endtry -%}
        '''.strip(),
        None,
    ),
    'try_complex-no_catch-no_error': (
        # language=jinja2
        '''
        {%- try -%}
            {%- set l = [] -%}
            {%- do l.append('t') -%}
            {%- for c in 'ry' -%}
                {%- do l.append(c) -%}
            {%- endfor -%}
            {{- l | join }}
        {%- endtry -%}
        '''.strip(),
        'try',
    ),
    'try-catch-no_error': (
        # language=jinja2
        '''
        {%- try -%}
            try
        {%- catch -%}
            catch
        {%- endtry %}
        '''.strip(),
        'try',
    ),
    'try-catch_complex-no_error': (
        # language=jinja2
        '''
        {%- try -%}
            try
        {%- catch -%}
            {%- set l = [] -%}
            {%- do l.append('c') -%}
            {%- for c in 'atch' -%}
                {%- do l.append(c) -%}
            {%- endfor -%}
            {{- l | join }}
        {%- endtry %}
        '''.strip(),
        'try',
    ),
    'try-no_catch-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- endtry -%}
        '''.strip(),
        '',
    ),
    'try-catch-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- catch -%}
            catch
        {%- endtry -%}
        '''.strip(),
        'catch',
    ),
    'try-catch_empty-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- catch -%}
        {%- endtry -%}
        '''.strip(),
        '',
    ),
    'try-catch_none-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- catch -%}
            {{ None }}
        {%- endtry -%}
        '''.strip(),
        None,
    ),
    'try-catch_complex-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- catch -%}
            {%- set l = [] -%}
            {%- do l.append('c') -%}
            {%- for c in 'atch' -%}
                {%- do l.append(c) -%}
            {%- endfor -%}
            {{- l | join }}
        {%- endtry -%}
        '''.strip(),
        'catch',
    ),
    'try-catch_exception-error': (
        # language=jinja2
        '''
        {%- try -%}
            {{- i_do_not_exist_and_throw_an_error -}}
            try
        {%- catch -%}
            catch: {{ exception -}}
        {%- endtry -%}
        '''.strip(),
        "catch: 'i_do_not_exist_and_throw_an_error' is undefined",
    ),

    '_on_catch-scoping-after': (
        # language=jinja2
        '''
        {%- try -%}
        {%- catch -%}
        {%- endtry -%}
        {{- _on_catch is defined -}}
        '''.strip(),
        False,
    ),

    # TODO: use inaccessible name to avoid exposing catch handler
    # '_on_catch-scoping-inside_try': (
    #     # language=jinja2
    #     '''
    #     {%- try -%}
    #       {{- _on_catch is defined -}}
    #     {%- catch -%}
    #     {%- endtry -%}
    #     '''.strip(),
    #     False,
    # ),
    # '_on_catch-scoping-inside_catch': (
    #     # language=jinja2
    #     '''
    #     {%- try -%}
    #     {%- catch -%}
    #       {{- _on_catch is defined -}}
    #     {%- endtry -%}
    #     '''.strip(),
    #     False,
    # ),
}


@pytest.mark.parametrize(('source', 'expected'), TEST_CASES.values(), ids=TEST_CASES.keys())
def test_sync_try_catch(sync_env, preprocess_expected, source, expected):
    template = sync_env.from_string(source)

    actual = template.render()
    expected = preprocess_expected(expected)
    assert expected == actual


@pytest.mark.asyncio
@pytest.mark.parametrize(('source', 'expected'), TEST_CASES.values(), ids=TEST_CASES.keys())
async def test_async_try_catch(async_env, preprocess_expected, source, expected):
    template = async_env.from_string(source)

    actual = await template.render_async()
    expected = preprocess_expected(expected)
    assert expected == actual
