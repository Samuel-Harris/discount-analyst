### RenderNumberConfig

Bases: `TypedDict`

A configuration for rendering a particular score or metric in an Evaluation report.

See the implementation of `_RenderNumber` for more clarity on how these parameters affect the rendering.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
class RenderNumberConfig(TypedDict, total=False):
    """A configuration for rendering a particular score or metric in an Evaluation report.

    See the implementation of `_RenderNumber` for more clarity on how these parameters affect the rendering.
    """

    value_formatter: str | Callable[[float | int], str]
    """The logic to use for formatting values.

    * If not provided, format as ints if all values are ints, otherwise at least one decimal place and at least four significant figures.
    * You can also use a custom string format spec, e.g. '{:.3f}'
    * You can also use a custom function, e.g. lambda x: f'{x:.3f}'
    """
    diff_formatter: str | Callable[[float | int, float | int], str | None] | None
    """The logic to use for formatting details about the diff.

    The strings produced by the value_formatter will always be included in the reports, but the diff_formatter is
    used to produce additional text about the difference between the old and new values, such as the absolute or
    relative difference.

    * If not provided, format as ints if all values are ints, otherwise at least one decimal place and at least four
        significant figures, and will include the percentage change.
    * You can also use a custom string format spec, e.g. '{:+.3f}'
    * You can also use a custom function, e.g. lambda x: f'{x:+.3f}'.
        If this function returns None, no extra diff text will be added.
    * You can also use None to never generate extra diff text.
    """
    diff_atol: float
    """The absolute tolerance for considering a difference "significant".

    A difference is "significant" if `abs(new - old) < self.diff_atol + self.diff_rtol * abs(old)`.

    If a difference is not significant, it will not have the diff styles applied. Note that we still show
    both the rendered before and after values in the diff any time they differ, even if the difference is not
    significant. (If the rendered values are exactly the same, we only show the value once.)

    If not provided, use 1e-6.
    """
    diff_rtol: float
    """The relative tolerance for considering a difference "significant".

    See the description of `diff_atol` for more details about what makes a difference "significant".

    If not provided, use 0.001 if all values are ints, otherwise 0.05.
    """
    diff_increase_style: str
    """The style to apply to diffed values that have a significant increase.

    See the description of `diff_atol` for more details about what makes a difference "significant".

    If not provided, use green for scores and red for metrics. You can also use arbitrary `rich` styles, such as "bold red".
    """
    diff_decrease_style: str
    """The style to apply to diffed values that have significant decrease.

    See the description of `diff_atol` for more details about what makes a difference "significant".

    If not provided, use red for scores and green for metrics. You can also use arbitrary `rich` styles, such as "bold red".
    """

```

#### value_formatter

```python
value_formatter: str | Callable[[float | int], str]

```

The logic to use for formatting values.

- If not provided, format as ints if all values are ints, otherwise at least one decimal place and at least four significant figures.
- You can also use a custom string format spec, e.g. '{:.3f}'
- You can also use a custom function, e.g. lambda x: f'{x:.3f}'

#### diff_formatter

```python
diff_formatter: (
    str
    | Callable[[float | int, float | int], str | None]
    | None
)

```

The logic to use for formatting details about the diff.

The strings produced by the value_formatter will always be included in the reports, but the diff_formatter is used to produce additional text about the difference between the old and new values, such as the absolute or relative difference.

- If not provided, format as ints if all values are ints, otherwise at least one decimal place and at least four significant figures, and will include the percentage change.
- You can also use a custom string format spec, e.g. '{:+.3f}'
- You can also use a custom function, e.g. lambda x: f'{x:+.3f}'. If this function returns None, no extra diff text will be added.
- You can also use None to never generate extra diff text.

#### diff_atol

```python
diff_atol: float

```

The absolute tolerance for considering a difference "significant".

A difference is "significant" if `abs(new - old) < self.diff_atol + self.diff_rtol * abs(old)`.

If a difference is not significant, it will not have the diff styles applied. Note that we still show both the rendered before and after values in the diff any time they differ, even if the difference is not significant. (If the rendered values are exactly the same, we only show the value once.)

If not provided, use 1e-6.

#### diff_rtol

```python
diff_rtol: float

```

The relative tolerance for considering a difference "significant".

See the description of `diff_atol` for more details about what makes a difference "significant".

If not provided, use 0.001 if all values are ints, otherwise 0.05.

#### diff_increase_style

```python
diff_increase_style: str

```

The style to apply to diffed values that have a significant increase.

See the description of `diff_atol` for more details about what makes a difference "significant".

If not provided, use green for scores and red for metrics. You can also use arbitrary `rich` styles, such as "bold red".

#### diff_decrease_style

```python
diff_decrease_style: str

```

The style to apply to diffed values that have significant decrease.

See the description of `diff_atol` for more details about what makes a difference "significant".

If not provided, use red for scores and green for metrics. You can also use arbitrary `rich` styles, such as "bold red".
