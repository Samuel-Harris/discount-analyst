## Datasets and Cases

In Pydantic Evals, everything begins with Datasets and Cases:

- **Dataset**: A collection of test Cases designed for the evaluation of a specific task or function
- **Case**: A single test scenario corresponding to Task inputs, with optional expected outputs, metadata, and case-specific evaluators

simple_eval_dataset.py

```python
from pydantic_evals import Case, Dataset

case1 = Case(
    name='simple_case',
    inputs='What is the capital of France?',
    expected_output='Paris',
    metadata={'difficulty': 'easy'},
)

dataset = Dataset(cases=[case1])

```

_(This example is complete, it can be run "as is")_

See [Dataset Management](how-to/dataset-management/) to learn about saving, loading, and generating datasets.
