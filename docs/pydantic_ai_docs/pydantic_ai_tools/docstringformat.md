### DocstringFormat

```python
DocstringFormat: TypeAlias = Literal[
    "google", "numpy", "sphinx", "auto"
]

```

Supported docstring formats.

- `'google'` â€” [Google-style](https://google.github.io/styleguide/pyguide.html#381-docstrings) docstrings.
- `'numpy'` â€” [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings.
- `'sphinx'` â€” [Sphinx-style](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format) docstrings.
- `'auto'` â€” Automatically infer the format based on the structure of the docstring.
