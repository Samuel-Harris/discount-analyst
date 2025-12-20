### Agent and Toolset Requirements

Each agent instance must have a unique `name` so DBOS can correctly resume workflows after a failure or restart.

Tools and event stream handlers are not automatically wrapped by DBOS. You can decide how to integrate them:

- Decorate with `@DBOS.step` if the function involves non-determinism or I/O.
- Skip the decorator if durability isn't needed, so you avoid the extra DB checkpoint write.
- If the function needs to enqueue tasks or invoke other DBOS workflows, run it inside the agent's main workflow (not as a step).

Other than that, any agent and toolset will just work!
