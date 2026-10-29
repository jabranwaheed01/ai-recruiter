from app.services.vapi_service import client


def create_greeting_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - Greeting",
        first_message="Hello, this is the AI recruiting assistant calling regarding your job application. Is this a good time to speak?",
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional and friendly AI recruiting assistant. "
                        "Introduce yourself clearly, explain that you are calling about "
                        "the candidate's job application, and ask whether they can speak. "
                        "Respect the candidate's choice if they are busy or do not want "
                        "to continue. Never invent candidate information. "
                        "Do not ask for sensitive personal information during the greeting. "
                        "If the candidate agrees, explain that you will proceed with "
                        "identity verification and eligibility screening."
                    ),
                }
            ],
            "temperature": 0.3,
            "max_tokens": 250,
        },
        voice={
            "provider": "vapi",
            "voice_id": "Elliot",
        },
        transcriber={
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        first_message_mode="assistant-speaks-first",
        end_call_message="Thank you for your time. Have a nice day!",
        max_duration_seconds=300,
    )

    print("Greeting Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_greeting_assistant()
