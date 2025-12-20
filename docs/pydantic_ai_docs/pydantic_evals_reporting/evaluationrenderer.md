### EvaluationRenderer

A class for rendering an EvalReport or the diff between two EvalReports.

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
@dataclass(kw_only=True)
class EvaluationRenderer:
    """A class for rendering an EvalReport or the diff between two EvalReports."""

    # Columns to include
    include_input: bool
    include_metadata: bool
    include_expected_output: bool
    include_output: bool
    include_durations: bool
    include_total_duration: bool

    # Rows to include
    include_removed_cases: bool
    include_averages: bool

    input_config: RenderValueConfig
    metadata_config: RenderValueConfig
    output_config: RenderValueConfig
    score_configs: dict[str, RenderNumberConfig]
    label_configs: dict[str, RenderValueConfig]
    metric_configs: dict[str, RenderNumberConfig]
    duration_config: RenderNumberConfig

    # Data to include
    include_reasons: bool  # only applies to reports, not to diffs

    include_error_message: bool
    include_error_stacktrace: bool
    include_evaluator_failures: bool

    def include_scores(self, report: EvaluationReport, baseline: EvaluationReport | None = None):
        return any(case.scores for case in self._all_cases(report, baseline))

    def include_labels(self, report: EvaluationReport, baseline: EvaluationReport | None = None):
        return any(case.labels for case in self._all_cases(report, baseline))

    def include_metrics(self, report: EvaluationReport, baseline: EvaluationReport | None = None):
        return any(case.metrics for case in self._all_cases(report, baseline))

    def include_assertions(self, report: EvaluationReport, baseline: EvaluationReport | None = None):
        return any(case.assertions for case in self._all_cases(report, baseline))

    def include_evaluator_failures_column(self, report: EvaluationReport, baseline: EvaluationReport | None = None):
        return self.include_evaluator_failures and any(
            case.evaluator_failures for case in self._all_cases(report, baseline)
        )

    def _all_cases(self, report: EvaluationReport, baseline: EvaluationReport | None) -> list[ReportCase]:
        if not baseline:
            return report.cases
        else:
            return report.cases + self._baseline_cases_to_include(report, baseline)

    def _baseline_cases_to_include(self, report: EvaluationReport, baseline: EvaluationReport) -> list[ReportCase]:
        if self.include_removed_cases:
            return baseline.cases
        report_case_names = {case.name for case in report.cases}
        return [case for case in baseline.cases if case.name in report_case_names]

    def _get_case_renderer(
        self, report: EvaluationReport, baseline: EvaluationReport | None = None
    ) -> ReportCaseRenderer:
        input_renderer = _ValueRenderer.from_config(self.input_config)
        metadata_renderer = _ValueRenderer.from_config(self.metadata_config)
        output_renderer = _ValueRenderer.from_config(self.output_config)
        score_renderers = self._infer_score_renderers(report, baseline)
        label_renderers = self._infer_label_renderers(report, baseline)
        metric_renderers = self._infer_metric_renderers(report, baseline)
        duration_renderer = _NumberRenderer.infer_from_config(
            self.duration_config, 'duration', [x.task_duration for x in self._all_cases(report, baseline)]
        )

        return ReportCaseRenderer(
            include_input=self.include_input,
            include_metadata=self.include_metadata,
            include_expected_output=self.include_expected_output,
            include_output=self.include_output,
            include_scores=self.include_scores(report, baseline),
            include_labels=self.include_labels(report, baseline),
            include_metrics=self.include_metrics(report, baseline),
            include_assertions=self.include_assertions(report, baseline),
            include_reasons=self.include_reasons,
            include_durations=self.include_durations,
            include_total_duration=self.include_total_duration,
            include_error_message=self.include_error_message,
            include_error_stacktrace=self.include_error_stacktrace,
            include_evaluator_failures=self.include_evaluator_failures_column(report, baseline),
            input_renderer=input_renderer,
            metadata_renderer=metadata_renderer,
            output_renderer=output_renderer,
            score_renderers=score_renderers,
            label_renderers=label_renderers,
            metric_renderers=metric_renderers,
            duration_renderer=duration_renderer,
        )

    # TODO(DavidM): in v2, change the return type here to RenderableType
    def build_table(self, report: EvaluationReport, *, with_title: bool = True) -> Table:
        """Build a table for the report.

        Args:
            report: The evaluation report to render
            with_title: Whether to include the title in the table (default True)

        Returns:
            A Rich Table object
        """
        case_renderer = self._get_case_renderer(report)

        title = f'Evaluation Summary: {report.name}' if with_title else ''
        table = case_renderer.build_base_table(title)

        for case in report.cases:
            table.add_row(*case_renderer.build_row(case))

        if self.include_averages:  # pragma: no branch
            average = report.averages()
            if average:  # pragma: no branch
                table.add_row(*case_renderer.build_aggregate_row(average))

        return table

    # TODO(DavidM): in v2, change the return type here to RenderableType
    def build_diff_table(
        self, report: EvaluationReport, baseline: EvaluationReport, *, with_title: bool = True
    ) -> Table:
        """Build a diff table comparing report to baseline.

        Args:
            report: The evaluation report to compare
            baseline: The baseline report to compare against
            with_title: Whether to include the title in the table (default True)

        Returns:
            A Rich Table object
        """
        report_cases = report.cases
        baseline_cases = self._baseline_cases_to_include(report, baseline)

        report_cases_by_id = {case.name: case for case in report_cases}
        baseline_cases_by_id = {case.name: case for case in baseline_cases}

        diff_cases: list[tuple[ReportCase, ReportCase]] = []
        removed_cases: list[ReportCase] = []
        added_cases: list[ReportCase] = []

        for case_id in sorted(set(baseline_cases_by_id.keys()) | set(report_cases_by_id.keys())):
            maybe_baseline_case = baseline_cases_by_id.get(case_id)
            maybe_report_case = report_cases_by_id.get(case_id)
            if maybe_baseline_case and maybe_report_case:
                diff_cases.append((maybe_baseline_case, maybe_report_case))
            elif maybe_baseline_case:
                removed_cases.append(maybe_baseline_case)
            elif maybe_report_case:
                added_cases.append(maybe_report_case)
            else:  # pragma: no cover
                assert False, 'This should be unreachable'

        case_renderer = self._get_case_renderer(report, baseline)
        diff_name = baseline.name if baseline.name == report.name else f'{baseline.name} â†’ {report.name}'

        title = f'Evaluation Diff: {diff_name}' if with_title else ''
        table = case_renderer.build_base_table(title)

        for baseline_case, new_case in diff_cases:
            table.add_row(*case_renderer.build_diff_row(new_case, baseline_case))
        for case in added_cases:
            row = case_renderer.build_row(case)
            row[0] = f'[green]+ Added Case[/]\n{row[0]}'
            table.add_row(*row)
        for case in removed_cases:
            row = case_renderer.build_row(case)
            row[0] = f'[red]- Removed Case[/]\n{row[0]}'
            table.add_row(*row)

        if self.include_averages:  # pragma: no branch
            report_average = ReportCaseAggregate.average(report_cases)
            baseline_average = ReportCaseAggregate.average(baseline_cases)
            table.add_row(*case_renderer.build_diff_aggregate_row(report_average, baseline_average))

        return table

    # TODO(DavidM): in v2, change the return type here to RenderableType
    def build_failures_table(self, report: EvaluationReport) -> Table:
        case_renderer = self._get_case_renderer(report)
        table = case_renderer.build_failures_table('Case Failures')
        for case in report.failures:
            table.add_row(*case_renderer.build_failure_row(case))

        return table

    def _infer_score_renderers(
        self, report: EvaluationReport, baseline: EvaluationReport | None
    ) -> dict[str, _NumberRenderer]:
        all_cases = self._all_cases(report, baseline)

        values_by_name: dict[str, list[float | int]] = {}
        for case in all_cases:
            for k, score in case.scores.items():
                values_by_name.setdefault(k, []).append(score.value)

        all_renderers: dict[str, _NumberRenderer] = {}
        for name, values in values_by_name.items():
            merged_config = _DEFAULT_NUMBER_CONFIG.copy()
            merged_config.update(self.score_configs.get(name, {}))
            all_renderers[name] = _NumberRenderer.infer_from_config(merged_config, 'score', values)
        return all_renderers

    def _infer_label_renderers(
        self, report: EvaluationReport, baseline: EvaluationReport | None
    ) -> dict[str, _ValueRenderer]:
        all_cases = self._all_cases(report, baseline)
        all_names: set[str] = set()
        for case in all_cases:
            for k in case.labels:
                all_names.add(k)

        all_renderers: dict[str, _ValueRenderer] = {}
        for name in all_names:
            merged_config = _DEFAULT_VALUE_CONFIG.copy()
            merged_config.update(self.label_configs.get(name, {}))
            all_renderers[name] = _ValueRenderer.from_config(merged_config)
        return all_renderers

    def _infer_metric_renderers(
        self, report: EvaluationReport, baseline: EvaluationReport | None
    ) -> dict[str, _NumberRenderer]:
        all_cases = self._all_cases(report, baseline)

        values_by_name: dict[str, list[float | int]] = {}
        for case in all_cases:
            for k, v in case.metrics.items():
                values_by_name.setdefault(k, []).append(v)

        all_renderers: dict[str, _NumberRenderer] = {}
        for name, values in values_by_name.items():
            merged_config = _DEFAULT_NUMBER_CONFIG.copy()
            merged_config.update(self.metric_configs.get(name, {}))
            all_renderers[name] = _NumberRenderer.infer_from_config(merged_config, 'metric', values)
        return all_renderers

    def _infer_duration_renderer(
        self, report: EvaluationReport, baseline: EvaluationReport | None
    ) -> _NumberRenderer:  # pragma: no cover
        all_cases = self._all_cases(report, baseline)
        all_durations = [x.task_duration for x in all_cases]
        if self.include_total_duration:
            all_durations += [x.total_duration for x in all_cases]
        return _NumberRenderer.infer_from_config(self.duration_config, 'duration', all_durations)

```

#### build_table

```python
build_table(
    report: EvaluationReport, *, with_title: bool = True
) -> Table

```

Build a table for the report.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `report` | `EvaluationReport` | The evaluation report to render | _required_ | | `with_title` | `bool` | Whether to include the title in the table (default True) | `True` |

Returns:

| Type | Description | | --- | --- | | `Table` | A Rich Table object |

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
def build_table(self, report: EvaluationReport, *, with_title: bool = True) -> Table:
    """Build a table for the report.

    Args:
        report: The evaluation report to render
        with_title: Whether to include the title in the table (default True)

    Returns:
        A Rich Table object
    """
    case_renderer = self._get_case_renderer(report)

    title = f'Evaluation Summary: {report.name}' if with_title else ''
    table = case_renderer.build_base_table(title)

    for case in report.cases:
        table.add_row(*case_renderer.build_row(case))

    if self.include_averages:  # pragma: no branch
        average = report.averages()
        if average:  # pragma: no branch
            table.add_row(*case_renderer.build_aggregate_row(average))

    return table

```

#### build_diff_table

```python
build_diff_table(
    report: EvaluationReport,
    baseline: EvaluationReport,
    *,
    with_title: bool = True
) -> Table

```

Build a diff table comparing report to baseline.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `report` | `EvaluationReport` | The evaluation report to compare | _required_ | | `baseline` | `EvaluationReport` | The baseline report to compare against | _required_ | | `with_title` | `bool` | Whether to include the title in the table (default True) | `True` |

Returns:

| Type | Description | | --- | --- | | `Table` | A Rich Table object |

Source code in `pydantic_evals/pydantic_evals/reporting/__init__.py`

```python
def build_diff_table(
    self, report: EvaluationReport, baseline: EvaluationReport, *, with_title: bool = True
) -> Table:
    """Build a diff table comparing report to baseline.

    Args:
        report: The evaluation report to compare
        baseline: The baseline report to compare against
        with_title: Whether to include the title in the table (default True)

    Returns:
        A Rich Table object
    """
    report_cases = report.cases
    baseline_cases = self._baseline_cases_to_include(report, baseline)

    report_cases_by_id = {case.name: case for case in report_cases}
    baseline_cases_by_id = {case.name: case for case in baseline_cases}

    diff_cases: list[tuple[ReportCase, ReportCase]] = []
    removed_cases: list[ReportCase] = []
    added_cases: list[ReportCase] = []

    for case_id in sorted(set(baseline_cases_by_id.keys()) | set(report_cases_by_id.keys())):
        maybe_baseline_case = baseline_cases_by_id.get(case_id)
        maybe_report_case = report_cases_by_id.get(case_id)
        if maybe_baseline_case and maybe_report_case:
            diff_cases.append((maybe_baseline_case, maybe_report_case))
        elif maybe_baseline_case:
            removed_cases.append(maybe_baseline_case)
        elif maybe_report_case:
            added_cases.append(maybe_report_case)
        else:  # pragma: no cover
            assert False, 'This should be unreachable'

    case_renderer = self._get_case_renderer(report, baseline)
    diff_name = baseline.name if baseline.name == report.name else f'{baseline.name} â†’ {report.name}'

    title = f'Evaluation Diff: {diff_name}' if with_title else ''
    table = case_renderer.build_base_table(title)

    for baseline_case, new_case in diff_cases:
        table.add_row(*case_renderer.build_diff_row(new_case, baseline_case))
    for case in added_cases:
        row = case_renderer.build_row(case)
        row[0] = f'[green]+ Added Case[/]\n{row[0]}'
        table.add_row(*row)
    for case in removed_cases:
        row = case_renderer.build_row(case)
        row[0] = f'[red]- Removed Case[/]\n{row[0]}'
        table.add_row(*row)

    if self.include_averages:  # pragma: no branch
        report_average = ReportCaseAggregate.average(report_cases)
        baseline_average = ReportCaseAggregate.average(baseline_cases)
        table.add_row(*case_renderer.build_diff_aggregate_row(report_average, baseline_average))

    return table

```
