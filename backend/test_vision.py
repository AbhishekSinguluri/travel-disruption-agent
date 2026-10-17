from dotenv import load_dotenv
load_dotenv()
import os, asyncio, instructor
from groq import Groq
from app.schemas.booking import CanonicalBooking

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.JSON)
    b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    models = ["llama-3.2-90b-vision", "llama-3.2-11b-vision", "llama-3.2-90b-vision-preview"]
    for m in models:
        print("Testing", m)
        try:
            res = client.chat.completions.create(
                model=m,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract details"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                        ]
                    }
                ],
                response_model=CanonicalBooking,
            )
            print("Success:", m)
            break
        except Exception as e:
            print("ERROR:", m, str(e))

if __name__ == "__main__":
    asyncio.run(main())
