### Dataset

Bases: `BaseModel`, `Generic[InputsT, OutputT, MetadataT]`

A dataset of test cases.

Datasets allow you to organize a collection of test cases and evaluate them against a task function. They can be loaded from and saved to YAML or JSON files, and can have dataset-level evaluators that apply to all cases.

Example:

```python
