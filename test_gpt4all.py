from gpt4all import GPT4All

model = GPT4All("orca-mini-3b-gguf2-q4_0")

response = model.generate(
    "Explique brièvement le rôle d'une application mobile",
    max_tokens=120
)

print(response)