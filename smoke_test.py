from openai import OpenAI

# llama-server does not check the key, but the client needs one
client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

response = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "Say hello"}],
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

print(response.choices[0].message.content)
