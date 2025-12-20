## OpenAI

When using the OpenAIChatModel, text output inside `<think>` tags are converted to ThinkingPart objects. You can customize the tags using the thinking_tags field on the [model profile](../models/openai/#model-profile).

Some [OpenAI-compatible model providers](../models/openai/#openai-compatible-models) might also support native thinking parts that are not delimited by tags. Instead, they are sent and received as separate, custom fields in the API. Typically, if you are calling the model via the `<provider>:<model>` shorthand, Pydantic AI handles it for you. Nonetheless, you can still configure the fields with openai_chat_thinking_field.

If your provider recommends to send back these custom fields not changed, for caching or interleaved thinking benefits, you can also achieve this with openai_chat_send_back_thinking_parts.
