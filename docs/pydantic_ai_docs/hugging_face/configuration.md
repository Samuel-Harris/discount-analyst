## Configuration

To use [Hugging Face](https://huggingface.co/) inference, you'll need to set up an account which will give you [free tier](https://huggingface.co/docs/inference-providers/pricing) allowance on [Inference Providers](https://huggingface.co/docs/inference-providers). To setup inference, follow these steps:

1. Go to [Hugging Face](https://huggingface.co/join) and sign up for an account.
1. Create a new access token in [Hugging Face](https://huggingface.co/settings/tokens).
1. Set the `HF_TOKEN` environment variable to the token you just created.

Once you have a Hugging Face access token, you can set it as an environment variable:

```bash
export HF_TOKEN='hf_token'

```
