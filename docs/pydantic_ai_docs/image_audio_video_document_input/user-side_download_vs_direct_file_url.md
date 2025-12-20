## User-side download vs. direct file URL

When you provide a URL using any of `ImageUrl`, `AudioUrl`, `VideoUrl` or `DocumentUrl`, Pydantic AI will typically send the URL directly to the model API so that the download happens on their side.

Some model APIs do not support file URLs at all or for specific file types. In the following cases, Pydantic AI will download the file content and send it as part of the API request instead:

- OpenAIChatModel: `AudioUrl` and `DocumentUrl`
- OpenAIResponsesModel: All URLs
- AnthropicModel: `DocumentUrl` with media type `text/plain`
- GoogleModel using GLA (Gemini Developer API): All URLs except YouTube video URLs and files uploaded to the [Files API](https://ai.google.dev/gemini-api/docs/files).
- BedrockConverseModel: All URLs

If the model API supports file URLs but may not be able to download a file because of crawling or access restrictions, you can instruct Pydantic AI to download the file content and send that instead of the URL by enabling the `force_download` flag on the URL object. For example, GoogleModel on Vertex AI limits YouTube video URLs to one URL per request.
