from app.services.vapi_service import client
from app.config import VAPI_SCHEDULING_ASSISTANT_ID


def create_screening_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - Eligibility Screening",
        first_message=(
            "Now I'd like to ask a few questions about your experience "
            "and qualifications for the role. Is that okay?"
        ),
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional and friendly AI recruitment assistant. "
                        "Ask concise, job-related questions about relevant experience, "
                        "skills, education, required qualifications, work authorization "
                        "where legally appropriate, and availability. "
                        "Assess candidates only against explicit job requirements supplied "
                        "by the system. Never invent requirements or make a final eligibility "
                        "decision without job criteria and candidate answers. "
                        "Never discriminate based on protected characteristics. "
                        "If requirements are missing, collect answers and mark the outcome "
                        "as pending review. Be respectful and allow the candidate to decline. "
                        "After completing the screening questions, summarize the candidate's "
                        "responses and ask whether they would like to discuss an interview. "
                        "If they agree, smoothly continue the conversation with interview "
                        "scheduling. "
                        "Never mention internal assistants, agents, handoffs, transfers, "
                        "or AI squad architecture. "
                        "Never say 'I'll connect you to the scheduling assistant' or "
                        "similar phrases. "
                        "The conversation must feel like one continuous interaction. "
                        "Never claim the candidate passed screening unless the required "
                        "job criteria have actually been evaluated."
                    )
                }
            ],

            "assistantDestinations": [
            {
                "type": "assistant",
                        "assistantName": "AI Recruiter - Interview Scheduling",
                        "message": "",
                        "description": "Transfer the user to the DOB Confirmation Assistant"
            }
        ],
          
            "temperature": 0.3,
            "max_tokens": 350,
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
        end_call_message="Thank you for answering the screening questions.",
        max_duration_seconds=600,
    )

    print("Screening Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_screening_assistant()
