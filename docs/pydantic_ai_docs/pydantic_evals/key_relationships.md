### Key Relationships

1. **Dataset â†’ Cases**: One Dataset contains many Cases
1. **Dataset â†’ Experiments**: One Dataset can be used across many Experiments over time
1. **Experiment â†’ Case results**: One Experiment generates results by executing each Case
1. **Experiment â†’ Task**: One Experiment evaluates one defined Task
1. **Experiment â†’ Evaluators**: One Experiment uses multiple Evaluators. Dataset-wide Evaluators are run against all Cases, and Case-specific Evaluators against their respective Cases
