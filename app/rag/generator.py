import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer(question, context):

    prompt = f"""
You are a helpful assistant answering questions about a YouTube video.

Answer ONLY using the provided video context.

If the answer is not present in the context, say:
"I couldn't find this information in the video."

Do not make up information.

Video Context:
{context}

Question:
{question}

Answer:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_completion_tokens=1024
    )

    return response.choices[0].message.content