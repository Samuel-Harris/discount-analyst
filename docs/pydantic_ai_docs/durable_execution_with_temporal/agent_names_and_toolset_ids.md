### Agent Names and Toolset IDs

To ensure that Temporal knows what code to run when an activity fails or is interrupted and then restarted, even if your code is changed in between, each activity needs to have a name that's stable and unique.

When `TemporalAgent` dynamically creates activities for the wrapped agent's model requests and toolsets (specifically those that implement their own tool listing and calling, i.e. FunctionToolset and MCPServer), their names are derived from the agent's name and the toolsets' ids. These fields are normally optional, but are required to be set when using Temporal. They should not be changed once the durable agent has been deployed to production as this would break active workflows.

Other than that, any agent and toolset will just work!
