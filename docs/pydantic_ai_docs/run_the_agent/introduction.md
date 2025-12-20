success_number = 18  # (3)!
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.output)  # (4)!
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.output)
#> False

```

1. Create an agent, which expects an integer dependency and produces a boolean output. This agent will have type `Agent[int, bool]`.
1. Define a tool that checks if the square is a winner. Here RunContext is parameterized with the dependency type `int`; if you got the dependency type wrong you'd get a typing error.
1. In reality, you might want to use a random number here e.g. `random.randint(0, 36)`.
1. `result.output` will be a boolean indicating if the square is a winner. Pydantic performs the output validation, and it'll be typed as a `bool` since its type is derived from the `output_type` generic parameter of the agent.

Agents are designed for reuse, like FastAPI Apps

You can instantiate one agent and use it globally throughout your application, as you would a small FastAPI app or an APIRouter, or dynamically create as many agents as you want. Both are valid and supported ways to use agents.
