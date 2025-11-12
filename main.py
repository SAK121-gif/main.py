from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import openai
import os

# Initialize FastAPI app
app = FastAPI(title="AI Agent Backend", description="Evolusis Backend Developer Assignment")

# Set your API keys as environment variables or replace with actual keys
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

class Query(BaseModel):
    query: str

# Function to detect query intent
def detect_intent(query: str) -> str:
    query_lower = query.lower()
    if "weather" in query_lower:
        return "weather"
    elif any(x in query_lower for x in ["who", "what", "when", "where", "wikipedia"]):
        return "wikipedia"
    elif "news" in query_lower:
        return "news"
    else:
        return "general"

# Fetch weather data
def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    res = requests.get(url)
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Weather API call failed.")
    data = res.json()
    description = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    return f"It's {temp}°C and {description} in {city.title()} today."

# Fetch Wikipedia summary
def get_wikipedia_summary(query: str):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        return data.get("extract", "No information found.")
    else:
        return "Sorry, I couldn't find information on that topic."

# Use LLM (OpenAI GPT)
def ask_llm(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

@app.post("/ask")
def ask_agent(request: Query):
    query = request.query
    intent = detect_intent(query)
    reasoning = ""
    answer = ""

    try:
        if intent == "weather":
            city = query.split("in")[-1].strip().replace("today", "").strip()
            reasoning = f"The user asked about weather, so I fetched data from OpenWeather API."
            answer = get_weather(city)
        elif intent == "wikipedia":
            reasoning = f"The user asked a factual question, so I searched Wikipedia."
            answer = get_wikipedia_summary(query)
        elif intent == "news":
            reasoning = f"The user asked for recent updates, so I used the News API."
            answer = "News fetching not implemented in this version."
        else:
            reasoning = "The user asked a general question, so I used GPT reasoning."
            answer = ask_llm(query)

        return {"reasoning": reasoning, "answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
