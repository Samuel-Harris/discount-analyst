### ReportCaseAggregate

Bases: `BaseModel`

A synthetic case that summarizes a set of cases.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
class ReportCaseAggregate(BaseModel):
    """A synthetic case that summarizes a set of cases."""

    name: str

    scores: dict[str, float | int]
    labels: dict[str, dict[str, float]]
    metrics: dict[str, float | int]
    assertions: float | None
    task_duration: float
    total_duration: float

    @staticmethod
    def average(cases: list[ReportCase]) -> ReportCaseAggregate:
        """Produce a synthetic "summary" case by averaging quantitative attributes."""
        num_cases = len(cases)
        if num_cases == 0:
            return ReportCaseAggregate(
                name='Averages',
                scores={},
                labels={},
                metrics={},
                assertions=None,
                task_duration=0.0,
                total_duration=0.0,
            )

        def _scores_averages(scores_by_name: list[dict[str, int | float | bool]]) -> dict[str, float]:
            counts_by_name: dict[str, int] = defaultdict(int)
            sums_by_name: dict[str, float] = defaultdict(float)
            for sbn in scores_by_name:
                for name, score in sbn.items():
                    counts_by_name[name] += 1
                    sums_by_name[name] += score
            return {name: sums_by_name[name] / counts_by_name[name] for name in sums_by_name}

        def _labels_averages(labels_by_name: list[dict[str, str]]) -> dict[str, dict[str, float]]:
            counts_by_name: dict[str, int] = defaultdict(int)
            sums_by_name: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
            for lbn in labels_by_name:
                for name, label in lbn.items():
                    counts_by_name[name] += 1
                    sums_by_name[name][label] += 1
            return {
                name: {value: count / counts_by_name[name] for value, count in sums_by_name[name].items()}
                for name in sums_by_name
            }

        average_task_duration = sum(case.task_duration for case in cases) / num_cases
        average_total_duration = sum(case.total_duration for case in cases) / num_cases

        # average_assertions: dict[str, float] = _scores_averages([{k: v.value for k, v in case.scores.items()} for case in cases])
        average_scores: dict[str, float] = _scores_averages(
            [{k: v.value for k, v in case.scores.items()} for case in cases]
        )
        average_labels: dict[str, dict[str, float]] = _labels_averages(
            [{k: v.value for k, v in case.labels.items()} for case in cases]
        )
        average_metrics: dict[str, float] = _scores_averages([case.metrics for case in cases])

        average_assertions: float | None = None
        n_assertions = sum(len(case.assertions) for case in cases)
        if n_assertions > 0:
            n_passing = sum(1 for case in cases for assertion in case.assertions.values() if assertion.value)
            average_assertions = n_passing / n_assertions

        return ReportCaseAggregate(
            name='Averages',
            scores=average_scores,
            labels=average_labels,
            metrics=average_metrics,
            assertions=average_assertions,
            task_duration=average_task_duration,
            total_duration=average_total_duration,
        )

```

#### average

```python
average(cases: list[ReportCase]) -> ReportCaseAggregate

```

Produce a synthetic "summary" case by averaging quantitative attributes.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
@staticmethod
def average(cases: list[ReportCase]) -> ReportCaseAggregate:
    """Produce a synthetic "summary" case by averaging quantitative attributes."""
    num_cases = len(cases)
    if num_cases == 0:
        return ReportCaseAggregate(
            name='Averages',
            scores={},
            labels={},
            metrics={},
            assertions=None,
            task_duration=0.0,
            total_duration=0.0,
        )

    def _scores_averages(scores_by_name: list[dict[str, int | float | bool]]) -> dict[str, float]:
        counts_by_name: dict[str, int] = defaultdict(int)
        sums_by_name: dict[str, float] = defaultdict(float)
        for sbn in scores_by_name:
            for name, score in sbn.items():
                counts_by_name[name] += 1
                sums_by_name[name] += score
        return {name: sums_by_name[name] / counts_by_name[name] for name in sums_by_name}

    def _labels_averages(labels_by_name: list[dict[str, str]]) -> dict[str, dict[str, float]]:
        counts_by_name: dict[str, int] = defaultdict(int)
        sums_by_name: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for lbn in labels_by_name:
            for name, label in lbn.items():
                counts_by_name[name] += 1
                sums_by_name[name][label] += 1
        return {
            name: {value: count / counts_by_name[name] for value, count in sums_by_name[name].items()}
            for name in sums_by_name
        }

    average_task_duration = sum(case.task_duration for case in cases) / num_cases
    average_total_duration = sum(case.total_duration for case in cases) / num_cases

    # average_assertions: dict[str, float] = _scores_averages([{k: v.value for k, v in case.scores.items()} for case in cases])
    average_scores: dict[str, float] = _scores_averages(
        [{k: v.value for k, v in case.scores.items()} for case in cases]
    )
    average_labels: dict[str, dict[str, float]] = _labels_averages(
        [{k: v.value for k, v in case.labels.items()} for case in cases]
    )
    average_metrics: dict[str, float] = _scores_averages([case.metrics for case in cases])

    average_assertions: float | None = None
    n_assertions = sum(len(case.assertions) for case in cases)
    if n_assertions > 0:
        n_passing = sum(1 for case in cases for assertion in case.assertions.values() if assertion.value)
        average_assertions = n_passing / n_assertions

    return ReportCaseAggregate(
        name='Averages',
        scores=average_scores,
        labels=average_labels,
        metrics=average_metrics,
        assertions=average_assertions,
        task_duration=average_task_duration,
        total_duration=average_total_duration,
    )

```
