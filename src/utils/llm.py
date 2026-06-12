from langchain_core.messages import AIMessage, ToolMessage
model_tokenizer = None

def get_context_length(
    model: str
) -> int:
    """Return the length of the context window for the specified model.
    Args:
        model (str): The model name.
    Returns:
        int: The length of the context window.
    """
    
    if "gpt-4o" in model:
        return 128e3
    elif "gemini-2.0" in model:
        return 1e6
    else:
        return 128e3
    
def count_tokens(
    text: str,
    model_name: str | None = None
) -> int:
    """Return the number of tokens in the text.
    Args:
        text (str): The text.
    Returns:
        int: The number of tokens.
    """
    global model_tokenizer
    
    if model_tokenizer is None:
        import tiktoken
        model_tokenizer = tiktoken.encoding_for_model("gpt-4o-mini") # TODO: Get the tokenizer of the selected model
    
    return len(model_tokenizer.encode(text))

def validate_messages_history(
    messages: list
) -> list:
    """Validate that all tool calls in AIMessages have a corresponding ToolMessage."""
    all_tool_calls = [
        tool_call
        for message in messages
        if isinstance(message, AIMessage)
        for tool_call in message.tool_calls
    ]
    tool_call_ids_with_results = {
        message.tool_call_id for message in messages if isinstance(message, ToolMessage)
    }
    tool_calls_without_results = [
        tool_call
        for tool_call in all_tool_calls
        if tool_call["id"] not in tool_call_ids_with_results
    ]
    
    # Remove any tool calls without results
    for message in messages:
        if isinstance(message, AIMessage):
            # Filter out tool calls that do not have results
            filtered_tool_calls = [
                tool_call for tool_call in message.tool_calls
                if tool_call["id"] in tool_call_ids_with_results
            ]
            message.tool_calls = filtered_tool_calls
    
    return messages