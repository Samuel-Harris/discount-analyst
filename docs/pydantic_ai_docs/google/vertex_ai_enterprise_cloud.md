### Vertex AI (Enterprise/Cloud)

If you are an enterprise user, you can also use `GoogleModel` to access Gemini via Vertex AI.

This interface has a number of advantages over the Generative Language API:

1. The VertexAI API comes with more enterprise readiness guarantees.
1. You can [purchase provisioned throughput](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput#purchase-provisioned-throughput) with Vertex AI to guarantee capacity.
1. If you're running Pydantic AI inside GCP, you don't need to set up authentication, it should "just work".
1. You can decide which region to use, which might be important from a regulatory perspective, and might improve latency.

You can authenticate using [application default credentials](https://cloud.google.com/docs/authentication/application-default-credentials), a service account, or an [API key](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys?usertype=expressmode).

Whichever way you authenticate, you'll need to have Vertex AI enabled in your GCP account.

#### Application Default Credentials

If you have the [`gcloud` CLI](https://cloud.google.com/sdk/gcloud) installed and configured, you can use `GoogleProvider` in Vertex AI mode by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/google-vertex:gemini-2.5-pro')
...

```

```python
from pydantic_ai import Agent

agent = Agent('google-vertex:gemini-2.5-pro')
...

```

Or you can explicitly create the provider and model:

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(vertexai=True)
model = GoogleModel('gemini-2.5-pro', provider=provider)
agent = Agent(model)
...

```

#### Service Account

To use a service account JSON file, explicitly create the provider and model:

google_model_service_account.py

```python
from google.oauth2 import service_account

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform'],
)
provider = GoogleProvider(credentials=credentials, project='your-project-id')
model = GoogleModel('gemini-2.5-flash', provider=provider)
agent = Agent(model)
...

```

#### API Key

To use Vertex AI with an API key, [create a key](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys?usertype=expressmode) and set it as an environment variable:

```bash
export GOOGLE_API_KEY=your-api-key

```

You can then use `GoogleModel` in Vertex AI mode by name:

[Learn about Gateway](../../gateway)

```python
from pydantic_ai import Agent

agent = Agent('gateway/google-vertex:gemini-2.5-pro')
...

```

```python
from pydantic_ai import Agent

agent = Agent('google-vertex:gemini-2.5-pro')
...

```

Or you can explicitly create the provider and model:

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(vertexai=True, api_key='your-api-key')
model = GoogleModel('gemini-2.5-pro', provider=provider)
agent = Agent(model)
...

```

#### Customizing Location or Project

You can specify the location and/or project when using Vertex AI:

google_model_location.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(vertexai=True, location='asia-east1', project='your-gcp-project-id')
model = GoogleModel('gemini-2.5-pro', provider=provider)
agent = Agent(model)
...

```

#### Model Garden

You can access models from the [Model Garden](https://cloud.google.com/model-garden?hl=en) that support the `generateContent` API and are available under your GCP project, including but not limited to Gemini, using one of the following `model_name` patterns:

- `{model_id}` for Gemini models
- `{publisher}/{model_id}`
- `publishers/{publisher}/models/{model_id}`
- `projects/{project}/locations/{location}/publishers/{publisher}/models/{model_id}`

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(
    project='your-gcp-project-id',
    location='us-central1',  # the region where the model is available
)
model = GoogleModel('meta/llama-3.3-70b-instruct-maas', provider=provider)
agent = Agent(model)
...

```
