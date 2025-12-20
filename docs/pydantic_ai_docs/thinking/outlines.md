## Outlines

Some local models run through Outlines include in their text output a thinking part delimited by tags. In that case, it will be handled by Pydantic AI that will separate the thinking part from the final answer without the need to specifically enable it. The thinking tags used by default are `"<think>"` and `"</think>"`. If your model uses different tags, you can specify them in the [model profile](../models/openai/#model-profile) using the thinking_tags field.

Outlines currently does not support thinking along with structured output. If you provide an `output_type`, the model text output will not contain a thinking part with the associated tags, and you may experience degraded performance.
