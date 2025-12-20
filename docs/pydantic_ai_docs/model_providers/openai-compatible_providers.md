## OpenAI-compatible Providers

In addition, many providers are compatible with the OpenAI API, and can be used with `OpenAIChatModel` in Pydantic AI:

- [Azure AI Foundry](../openai/#azure-ai-foundry)
- [Cerebras](../openai/#cerebras)
- [DeepSeek](../openai/#deepseek)
- [Fireworks AI](../openai/#fireworks-ai)
- [GitHub Models](../openai/#github-models)
- [Grok (xAI)](../openai/#grok-xai)
- [Heroku](../openai/#heroku-ai)
- [LiteLLM](../openai/#litellm)
- [Nebius AI Studio](../openai/#nebius-ai-studio)
- [Ollama](../openai/#ollama)
- [OVHcloud AI Endpoints](../openai/#ovhcloud-ai-endpoints)
- [Perplexity](../openai/#perplexity)
- [Together AI](../openai/#together-ai)
- [Vercel AI Gateway](../openai/#vercel-ai-gateway)

Pydantic AI also comes with [`TestModel`](../../api/models/test/) and [`FunctionModel`](../../api/models/function/) for testing and development.

To use each model provider, you need to configure your local environment and make sure you have the right packages installed. If you try to use the model without having done so, you'll be told what to install.
