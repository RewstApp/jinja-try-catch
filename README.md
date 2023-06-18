# jinja-try-catch
A Jinja2 extension providing exception handling within templates.

```jinja
{%- try -%}
  {{ 1 / 0 }}
{%- catch -%}
  Can't divide by zero!
{%- endtry -%}
```
```
Can't divide by zero!
```

This extension works in both sync and async environments, as well as the native variants, too.

# Quickstart
```shell
pip install jinja-try-catch
```

And add the `TryCatchExtension` to your `Environment` extensions list:
```python
import jinja2
from jinja_try_catch import TryCatchExtension

jinja_env = jinja2.Environment(extensions=[TryCatchExtension])
```


# Usage
### Suppressing errors
Simply omit the `{% catch %}` to silently swallow exceptions
```jinja
{%- try -%}
  {{ 1 / 0 }}
{%- endtry -%}
```
```
```

### Error messages
Define a `{% catch %}` to render something else if an exception is raised
```jinja
{%- try -%}
  {{ 1 / 0 }}
{%- catch -%}
  There are infinite zeroes, duh
{%- endtry -%}
```
```
There are infinite zeroes, duh
```

### Display exceptions
The raised exception is exposed within the `{% catch %}` through the `{{ exception }}` variable
```jinja
{%- try -%}
  {{ 1 / 0 }}
{%- catch -%}
  Uh-oh, an error occurred:
  {{ exception.__class__.__name__ }}: {{ exception }}
{%- endtry -%}
```
```
Uh-oh, an error occurred:
  ZeroDivisionError: division by zero
```
