import ollama

def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    return f"The weather in {city} is sunny."

response = ollama.chat(
    model='qwen2.5-coder:7b',
    messages=[{'role': 'user', 'content': 'What is the weather in Seoul?'}],
    tools=[get_weather]
)
print("Content:", repr(response.message.content))
print("Tool calls:", response.message.tool_calls)
