### Advanced Tool Returns

For scenarios where you need more control over both the tool's return value and the content sent to the model, you can use ToolReturn. This is particularly useful when you want to:

- Provide rich multi-modal content (images, documents, etc.) to the model as context
- Separate the programmatic return value from the model's context
- Include additional metadata that shouldn't be sent to the LLM

Here's an example of a computer automation tool that captures screenshots and provides visual feedback:

[Learn about Gateway](../gateway) advanced_tool_return.py

```python
import time
from pydantic_ai import Agent
from pydantic_ai import ToolReturn, BinaryContent

agent = Agent('gateway/openai:gpt-5')

@agent.tool_plain
def click_and_capture(x: int, y: int) -> ToolReturn:
    """Click at coordinates and show before/after screenshots."""
    # Take screenshot before action
    before_screenshot = capture_screen()

    # Perform click operation
    perform_click(x, y)
    time.sleep(0.5)  # Wait for UI to update

    # Take screenshot after action
    after_screenshot = capture_screen()

    return ToolReturn(
        return_value=f"Successfully clicked at ({x}, {y})",
        content=[
            f"Clicked at coordinates ({x}, {y}). Here's the comparison:",
            "Before:",
            BinaryContent(data=before_screenshot, media_type="image/png"),
            "After:",
            BinaryContent(data=after_screenshot, media_type="image/png"),
            "Please analyze the changes and suggest next steps."
        ],
        metadata={
            "coordinates": {"x": x, "y": y},
            "action_type": "click_and_capture",
            "timestamp": time.time()
        }
    )
