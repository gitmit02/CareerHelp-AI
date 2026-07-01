"""
CareerHelp Agent — minimal Google ADK 2.3.0 demo
==================================================

This is a standalone demo for the Kaggle Capstone. It is intentionally small:
one ADK agent, one tool. It mirrors the same career-analysis logic used in the
NaviGenAI production app (Node/Express + Groq), re-expressed as an ADK agent
so it can be evaluated with ADK's agent runtime / `adk web` / `adk run`.

NaviGenAI itself (the Node.js production app) is untouched — this folder is
fully separate.
"""

# Import json to parse structured JSON outputs returned by Groq completions API
import json
# Import os to fetch environmental variables like api keys
import os

# Import requests to handle sync HTTP client POST queries
import requests
# Import Agent from ADK to wrap instructions, descriptors, and tools in a standard agent runtime
from google.adk.agents import Agent
# Import LiteLlm from ADK to leverage LiteLLM provider wrappers (allowing Groq endpoint configurations)
from google.adk.models.lite_llm import LiteLlm

# Retrieve Groq credentials from environment state
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
# Define the model engine ID to use
GROQ_MODEL = "llama-3.3-70b-versatile"


def analyze_career(skills: str, interests: str, goal: str) -> dict:
    """Analyzes a user's skills, interests, and career goal and returns a
    personalized tech career recommendation.

    Args:
        skills: Comma-separated list of the user's current skills.
        interests: Comma-separated list of the user's interests.
        goal: The user's stated career goal.

    Returns:
        dict: A structured result with keys: careerPath, matchPercentage,
        careerDescription, skillGaps, learningResources, certifications,
        internships, jobRoles, portfolioProjects, salaryInsights, roadmap.
        On failure, returns {"error": "<message>"}.
    """
    # Verify that the required Groq credentials are set up in the environment
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY is not set. Add it to your .env file."}

    # Construct the query prompt for Llama 3.3 model engine detailing schema and content parameters
    prompt = f"""You are CareerHelp, an expert Career Navigation Agent for technology careers.

Analyze this user profile:
- Skills: {skills}
- Interests: {interests}
- Career Goal: {goal}

Determine the BEST-FIT technology career path based on the actual profile. Do NOT default to Data Analytics unless the profile strongly shows it.

Domains to consider: Web Development, Full Stack Development, AI/ML, Data Science, Data Analytics, Cybersecurity, Cloud Computing, DevOps, Blockchain, Mobile Development, UI/UX Design, Product Management, Game Development, Embedded Systems.

Return ONLY valid JSON, absolutely no markdown fences, no explanation, just raw JSON:
{{
  "careerPath": "exact career domain name",
  "matchPercentage": 85,
  "careerDescription": "2-3 sentences why this path fits this person specifically",
  "skillGaps": [
    {{"skill": "Skill Name", "priority": "high", "reason": "one sentence why needed"}}
  ],
  "learningResources": [
    {{"name": "Resource Name", "platform": "Platform/URL", "free": true}}
  ],
  "certifications": [
    {{"name": "Full Certification Name", "provider": "Issuing Organization", "cost": "Free / $X"}}
  ],
  "internships": [
    {{"role": "Internship Role Title", "platform": "Platform name", "type": "Remote/On-site/Hybrid", "stipend": "Paid - amount / Unpaid"}}
  ],
  "jobRoles": [
    {{"title": "Job Title", "level": "Entry-level", "description": "why this fits the profile"}}
  ],
  "portfolioProjects": [
    {{"title": "Project Name", "difficulty": "Beginner", "description": "what to build and why it matters", "skills": ["skill1", "skill2"]}}
  ],
  "salaryInsights": {{"entry": "range", "mid": "range", "senior": "range"}},
  "roadmap": [
    {{"phase": "Phase 1 - Foundation", "duration": "4-6 weeks", "description": "details", "tasks": ["task1", "task2"]}}
  ]
}}"""

    # Post query payload synchronously to the Groq Chat Completions endpoint
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.65,
            "max_tokens": 3200,
        },
        timeout=30,
    )

    # Check for HTTP 429 rate limits
    if response.status_code == 429:
        return {"error": "Rate limit reached. Please wait and try again."}
    # Check for general network status errors
    if not response.ok:
        return {"error": f"Groq API error: HTTP {response.status_code}"}

    # Extract the raw message content from response object JSON
    raw = response.json()["choices"][0]["message"]["content"]
    # Strip markdown wrappers if they exist in output
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        # Load cleaned string directly into a dictionary
        return json.loads(clean)
    except json.JSONDecodeError:
        # Fallback regex-like substring lookup targeting bounding braces if formatting was slightly off
        start, end = clean.find("{"), clean.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(clean[start : end + 1])
            except json.JSONDecodeError:
                pass
        # Return error if parsing is impossible
        return {"error": "Model returned invalid JSON. Please try again."}


# Define the ADK Agent structure, configuring the model engine client, description instructions, and registered tool methods
root_agent = Agent(
    name="careerhelp_agent",
    # Pass LiteLlm instance configured to run llama-3.3-70b-versatile via Groq provider
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    # General descriptive information about the agent behavior
    description=(
        "CareerHelp is a career navigation agent that analyzes a user's skills, "
        "interests, and career goal, then returns a personalized tech career "
        "roadmap: recommended path, skill gaps, learning resources, "
        "certifications, internships, job roles, portfolio projects, salary "
        "insights, and a phased action plan."
    ),
    # Instruction directing the runtime execution flow on how to consult tools and summarize results
    instruction=(
        "You are CareerHelp, a friendly career navigation assistant for people "
        "exploring technology careers.\n\n"
        "When a user describes their skills, interests, and career goal, call "
        "the analyze_career tool with those three values to generate a "
        "personalized roadmap.\n\n"
        "If the user hasn't given you all three (skills, interests, goal), ask "
        "for whichever is missing before calling the tool.\n\n"
        "After the tool returns, summarize the results conversationally: lead "
        "with the recommended career path and match score, then walk through "
        "the top 2-3 skill gaps, a couple of learning resources, one or two "
        "internship or job role suggestions, and the first phase of the "
        "roadmap. Keep it encouraging and concrete. If the tool returns an "
        "error, explain it plainly and suggest what to check (e.g. a missing "
        "API key)."
    ),
    # Register the analyze_career method as a callable tool for the Agent runtime
    tools=[analyze_career],
)