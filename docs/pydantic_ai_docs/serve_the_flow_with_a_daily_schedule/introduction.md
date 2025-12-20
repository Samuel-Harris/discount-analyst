if __name__ == '__main__':
    daily_report_flow.serve(
        name='daily-report-deployment',
        cron='0 9 * * *',  # Run daily at 9am
        parameters={'user_prompt': "Generate today's report"},
        tags=['production', 'reports'],
    )

```

1. Each flow run executes in an isolated process, and all inputs and dependencies must be serializable. Because Agent instances cannot be serialized, instantiate the agent inside the flow rather than at the module level.

The `serve()` method accepts scheduling options:

- **`cron`**: Cron schedule string (e.g., `'0 9 * * *'` for daily at 9am)
- **`interval`**: Schedule interval in seconds or as a timedelta
- **`rrule`**: iCalendar RRule schedule string

For production deployments with Docker, Kubernetes, or other infrastructure, use the flow's [`deploy()`](https://docs.prefect.io/v3/how-to-guides/deployments/deploy-via-python) method. See the [Prefect deployment documentation](https://docs.prefect.io/v3/how-to-guides/deployments/create-deploymentsy) for more information.
