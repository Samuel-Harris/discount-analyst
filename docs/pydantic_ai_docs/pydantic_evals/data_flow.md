### Data Flow

1. **Dataset creation**: Define cases and evaluators in YAML/JSON, or directly in Python
1. **Experiment execution**: Run `dataset.evaluate_sync(task_function)`
1. **Cases run**: Each Case is executed against the Task
1. **Evaluation**: Evaluators score the Task outputs for each Case
1. **Results**: All Case results are collected into a summary report

A metaphor

A useful metaphor (although not perfect) is to think of evals like a **Unit Testing** framework:

- **Cases + Evaluators** are your individual unit tests - each one defines a specific scenario you want to test, complete with inputs and expected outcomes. Just like a unit test, a case asks: _"Given this input, does my system produce the right output?"_
- **Datasets** are like test suites - they are the scaffolding that holds your unit tests together. They group related cases and define shared evaluation criteria that should apply across all tests in the suite.
- **Experiments** are like running your entire test suite and getting a report. When you execute `dataset.evaluate_sync(my_ai_function)`, you're running all your cases against your AI system and collecting the results - just like running `pytest` and getting a summary of passes, failures, and performance metrics.

The key difference from traditional unit testing is that AI systems are probabilistic. If you're type checking you'll still get a simple pass/fail, but scores for text outputs are likely qualitative and/or categorical, and more open to interpretation.

For a deeper understanding, see [Core Concepts](core-concepts/).
