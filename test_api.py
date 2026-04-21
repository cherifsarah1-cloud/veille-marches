import anthropic
client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=50,
    messages=[{"role": "user", "content": "Dis juste: OK"}]
)
print(msg.content[0].text)
