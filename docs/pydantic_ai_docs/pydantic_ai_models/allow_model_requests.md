### ALLOW_MODEL_REQUESTS

```python
ALLOW_MODEL_REQUESTS = True

```

Whether to allow requests to models.

This global setting allows you to disable request to most models, e.g. to make sure you don't accidentally make costly requests to a model during tests.

The testing models TestModel and FunctionModel are no affected by this setting.
