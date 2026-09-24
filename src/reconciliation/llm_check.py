from anthropic import Anthropic

from reconciliation.config import settings


def main() -> None:
    client = Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=50,
        messages=[{"role": "user", "content": "Rispondi solo con: connessione ok"}],
    )
    print(response.content[0].text)
    print(f"Token input: {response.usage.input_tokens}, output: {response.usage.output_tokens}")


if __name__ == "__main__":
    main()