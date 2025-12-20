## Stateful Graphs

The "state" concept in `pydantic-graph` provides an optional way to access and mutate an object (often a `dataclass` or Pydantic model) as nodes run in a graph. If you think of Graphs as a production line, then your state is the engine being passed along the line and built up by each node as the graph is run.

`pydantic-graph` provides state persistence, with the state recorded after each node is run. (See [State Persistence](#state-persistence).)

Here's an example of a graph which represents a vending machine where the user may insert coins and select a product to purchase.

vending_machine.py

```python
from __future__ import annotations

from dataclasses import dataclass

from rich.prompt import Prompt

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


@dataclass
class MachineState:  # (1)!
    user_balance: float = 0.0
    product: str | None = None


@dataclass
class InsertCoin(BaseNode[MachineState]):  # (3)!
    async def run(self, ctx: GraphRunContext[MachineState]) -> CoinsInserted:  # (16)!
        return CoinsInserted(float(Prompt.ask('Insert coins')))  # (4)!


@dataclass
class CoinsInserted(BaseNode[MachineState]):
    amount: float  # (5)!

    async def run(
        self, ctx: GraphRunContext[MachineState]
    ) -> SelectProduct | Purchase:  # (17)!
        ctx.state.user_balance += self.amount  # (6)!
        if ctx.state.product is not None:  # (7)!
            return Purchase(ctx.state.product)
        else:
            return SelectProduct()


@dataclass
class SelectProduct(BaseNode[MachineState]):
    async def run(self, ctx: GraphRunContext[MachineState]) -> Purchase:
        return Purchase(Prompt.ask('Select product'))


PRODUCT_PRICES = {  # (2)!
    'water': 1.25,
    'soda': 1.50,
    'crisps': 1.75,
    'chocolate': 2.00,
}


@dataclass
class Purchase(BaseNode[MachineState, None, None]):  # (18)!
    product: str

    async def run(
        self, ctx: GraphRunContext[MachineState]
    ) -> End | InsertCoin | SelectProduct:
        if price := PRODUCT_PRICES.get(self.product):  # (8)!
            ctx.state.product = self.product  # (9)!
            if ctx.state.user_balance >= price:  # (10)!
                ctx.state.user_balance -= price
                return End(None)
            else:
                diff = price - ctx.state.user_balance
                print(f'Not enough money for {self.product}, need {diff:0.2f} more')
                #> Not enough money for crisps, need 0.75 more
                return InsertCoin()  # (11)!
        else:
            print(f'No such product: {self.product}, try again')
            return SelectProduct()  # (12)!


vending_machine_graph = Graph(  # (13)!
    nodes=[InsertCoin, CoinsInserted, SelectProduct, Purchase]
)


async def main():
    state = MachineState()  # (14)!
    await vending_machine_graph.run(InsertCoin(), state=state)  # (15)!
    print(f'purchase successful item={state.product} change={state.user_balance:0.2f}')
    #> purchase successful item=crisps change=0.25

```

1. The state of the vending machine is defined as a dataclass with the user's balance and the product they've selected, if any.
1. A dictionary of products mapped to prices.
1. The `InsertCoin` node, BaseNode is parameterized with `MachineState` as that's the state used in this graph.
1. The `InsertCoin` node prompts the user to insert coins. We keep things simple by just entering a monetary amount as a float. Before you start thinking this is a toy too since it's using rich's Prompt.ask within nodes, see [below](#example-human-in-the-loop) for how control flow can be managed when nodes require external input.
1. The `CoinsInserted` node; again this is a dataclass with one field `amount`.
1. Update the user's balance with the amount inserted.
1. If the user has already selected a product, go to `Purchase`, otherwise go to `SelectProduct`.
1. In the `Purchase` node, look up the price of the product if the user entered a valid product.
1. If the user did enter a valid product, set the product in the state so we don't revisit `SelectProduct`.
1. If the balance is enough to purchase the product, adjust the balance to reflect the purchase and return End to end the graph. We're not using the run return type, so we call `End` with `None`.
1. If the balance is insufficient, go to `InsertCoin` to prompt the user to insert more coins.
1. If the product is invalid, go to `SelectProduct` to prompt the user to select a product again.
1. The graph is created by passing a list of nodes to Graph. Order of nodes is not important, but it can affect how [diagrams](#mermaid-diagrams) are displayed.
1. Initialize the state. This will be passed to the graph run and mutated as the graph runs.
1. Run the graph with the initial state. Since the graph can be run from any node, we must pass the start node â€” in this case, `InsertCoin`. Graph.run returns a GraphRunResult that provides the final data and a history of the run.
1. The return type of the node's run method is important as it is used to determine the outgoing edges of the node. This information in turn is used to render [mermaid diagrams](#mermaid-diagrams) and is enforced at runtime to detect misbehavior as soon as possible.
1. The return type of `CoinsInserted`'s run method is a union, meaning multiple outgoing edges are possible.
1. Unlike other nodes, `Purchase` can end the run, so the RunEndT generic parameter must be set. In this case it's `None` since the graph run return type is `None`.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

A [mermaid diagram](#mermaid-diagrams) for this graph can be generated with the following code:

vending_machine_diagram.py

```python
from vending_machine import InsertCoin, vending_machine_graph

vending_machine_graph.mermaid_code(start_node=InsertCoin)

```

The diagram generated by the above code is:

```
---
title: vending_machine_graph
---
stateDiagram-v2
  [*] --> InsertCoin
  InsertCoin --> CoinsInserted
  CoinsInserted --> SelectProduct
  CoinsInserted --> Purchase
  SelectProduct --> Purchase
  Purchase --> InsertCoin
  Purchase --> SelectProduct
  Purchase --> [*]
```

See [below](#mermaid-diagrams) for more information on generating diagrams.
