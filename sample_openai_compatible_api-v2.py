from openai import OpenAI

# *Prompt user for inputs*
base_url = input("Enter base URL (default: https://openrouter.ai/api/v1): ") or "https://openrouter.ai/api/v1"
api_key = input("Enter your API key: ")
model = input("Enter the model name (default: openai/gpt-3.5-turbo): ") or "openai/gpt-3.5-turbo"
system_prompt = input("Enter the system prompt (e.g., 'You are a helpful assistant'): ") or "You are a helpful assistant"
user_prompt = input("Enter your question or input for the AI: ")
temperature = float(input("Enter the temperature (default: 0.7, range: 0.0 to 1.0): ") or 0.7)

# *Initialize the OpenAI client*
client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

# *Create the completion request*
completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "",  # Optional. Site URL for rankings on openrouter.ai.
        "X-Title": "",       # Optional. Site title for rankings on openrouter.ai.
    },
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},  # *Add system prompt*
        {"role": "user", "content": user_prompt},      # *Add user prompt*
    ],
    temperature=temperature,  # *Set temperature*
)

# *Print the AI's response*
print(f"*AI Response*: {completion.choices[0].message.content}")
