### prompted_output_template

```python
prompted_output_template: str = dedent(
    "\n        Always respond with a JSON object that's compatible with this schema:\n\n        {schema}\n\n        Don't include any text or Markdown fencing before or after.\n        "
)

```

The instructions template to use for prompted structured output. The '{schema}' placeholder will be replaced with the JSON schema for the output.
