### GroqModelName

```python
GroqModelName = (
    str | ProductionGroqModelNames | PreviewGroqModelNames
)

```

Possible Groq model names.

Since Groq supports a variety of models and the list changes frequencly, we explicitly list the named models as of 2025-03-31 but allow any name in the type hints.

See <https://console.groq.com/docs/models> for an up to date date list of models and more details.
