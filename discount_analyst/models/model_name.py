from enum import StrEnum


class ModelName(StrEnum):
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_OPUS_4_6 = "claude-opus-4-6"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4_6 = "claude-haiku-4-6"
    GPT_5_1 = "gpt-5.1"
    GPT_5_2 = "gpt-5.2"
    GPT_5_4 = "gpt-5.4"
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    GEMINI_3_1_PRO_PREVIEW = "gemini-3.1-pro-preview"
    DEEPSEEK_V4_FLASH = "deepseek-v4-flash"
    DEEPSEEK_V4_PRO = "deepseek-v4-pro"
