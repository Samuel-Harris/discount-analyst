### Design

**FastA2A** is built on top of [Starlette](https://www.starlette.io), which means it's fully compatible with any ASGI server.

Given the nature of the A2A protocol, it's important to understand the design before using it, as a developer you'll need to provide some components:

- Storage: to save and load tasks, as well as store context for conversations
- Broker: to schedule tasks
- Worker: to execute tasks

Let's have a look at how those components fit together:

```
flowchart TB
    Server["HTTP Server"] <--> |Sends Requests/<br>Receives Results| TM

    subgraph CC[Core Components]
        direction RL
        TM["TaskManager<br>(coordinates)"] --> |Schedules Tasks| Broker
        TM <--> Storage
        Broker["Broker<br>(queues & schedules)"] <--> Storage["Storage<br>(persistence)"]
        Broker --> |Delegates Execution| Worker
    end

    Worker["Worker<br>(implementation)"]
```

FastA2A allows you to bring your own Storage, Broker and Worker.

#### Understanding Tasks and Context

In the A2A protocol:

- **Task**: Represents one complete execution of an agent. When a client sends a message to the agent, a new task is created. The agent runs until completion (or failure), and this entire execution is considered one task. The final output is stored as a task artifact.
- **Context**: Represents a conversation thread that can span multiple tasks. The A2A protocol uses a `context_id` to maintain conversation continuity:
- When a new message is sent without a `context_id`, the server generates a new one
- Subsequent messages can include the same `context_id` to continue the conversation
- All tasks sharing the same `context_id` have access to the complete message history

#### Storage Architecture

The Storage component serves two purposes:

1. **Task Storage**: Stores tasks in A2A protocol format, including their status, artifacts, and message history
1. **Context Storage**: Stores conversation context in a format optimized for the specific agent implementation

This design allows for agents to store rich internal state (e.g., tool calls, reasoning traces) as well as store task-specific A2A-formatted messages and artifacts.

For example, a Pydantic AI agent might store its complete internal message format (including tool calls and responses) in the context storage, while storing only the A2A-compliant messages in the task history.
