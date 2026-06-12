def format_gradio_tool_message(message):
    if not isinstance(message, str):
        return message

    # List of markdown special characters to escape
    markdown_chars = [
        '\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|', '>', '~'
    ]
    for char in markdown_chars:
        message = message.replace(char, f'\\{char}')
    return message
