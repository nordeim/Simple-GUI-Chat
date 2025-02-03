from openai import OpenAI

def multi_line_input(prompt):
    """Helper function to allow multi-line input."""
    print(prompt)
    print("Enter your text below. Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) to finish:")
    lines = []
    while True:
        try:
            line = input()
            lines.append(line)
        except EOFError:  # Detects Ctrl+D or Ctrl+Z to end input
            break
    return "\n".join(lines)

# *Prompt user for inputs with confirmation*
base_url = input("Enter base URL (default: https://openrouter.ai/api/v1): ") or "https://openrouter.ai/api/v1"
print(f"*Base URL*: {base_url}")  # Confirm the base URL

api_key = input("Enter your API key: ")
if not api_key.strip():  # Check if API key is empty
    print("*Error*: API key cannot be empty. Please provide a valid API key.")
    exit(1)
print(f"*API Key*: {'*' * len(api_key)}")  # Mask the API key for security

model = input("Enter the model name (default: deepseek/deepseek-r1:free): ") or "deepseek/deepseek-r1:free"
print(f"*Model*: {model}")  # Confirm the model

system_prompt = multi_line_input("Enter the system prompt (e.g., 'You are a helpful assistant'):")
system_prompt = system_prompt or "You are a helpful assistant"  # Default if empty
print(f"*System Prompt*: {system_prompt}")  # Confirm the system prompt

user_prompt = multi_line_input("Enter your question or input for the AI:")
print(f"*User Prompt*: {user_prompt}")  # Confirm the user prompt

temperature = float(input("Enter the temperature (default: 0.8, range: 0.0 to 1.0): ") or 0.8)
print(f"*Temperature*: {temperature}")  # Confirm the temperature

# *Initialize the OpenAI client*
try:
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,  # Ensure the API key is correctly passed
    )
except Exception as e:
    print(f"*Error initializing OpenAI client*: {str(e)}")
    exit(1)

# *Create the completion request*
try:
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "",       # Optional. Site title for rankings on openrouter.ai.
        },
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},  # Add system prompt
            {"role": "user", "content": user_prompt},      # Add user prompt
        ],
        temperature=temperature,  # Set temperature
    )
    # *Print the AI's response*
    print(f"*AI Response*: {completion.choices[0].message.content}")
except Exception as e:
    print(f"*Error during API call*: {str(e)}")
  
