## Building a Custom Toolset

To define a fully custom toolset with its own logic to list available tools and handle them being called, you can subclass AbstractToolset and implement the get_tools() and call_tool() methods.

If you want to reuse a network connection or session across tool listings and calls during an agent run, you can implement **aenter**() and **aexit**().
