/**
 * server.js
 * Express Backend Server for CareerHelp AI
 * Handles static file hosting and acts as a proxy for the Groq Cloud API.
 */

// Import express to build our web server application
import express from "express";
// Import CORS (Cross-Origin Resource Sharing) middleware to allow backend access from other domains/ports
import cors from "cors";
// Import dotenv to load key-value pairs from the .env file into process.env
import dotenv from "dotenv";
// Import path to resolve file and folder paths correctly across operating systems
import path from "path";
// Import fileURLToPath to work with absolute file URLs in modern ES module scopes
import { fileURLToPath } from "url";

// Load environment variables from .env file (such as GROQ_API_KEY)
dotenv.config();

// ES module compatibility to get __dirname equivalent
// fileURLToPath converts import.meta.url to a file path string. path.dirname extracts the folder path.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Initialize our Express application instance
const app = express();

// Enable Cross-Origin Resource Sharing (CORS) for external api access
app.use(cors());

// Parse incoming JSON payloads in request bodies so we can access them via req.body
app.use(express.json());

// Serve static assets (index.html, styles, scripts) directly from the project root directory
// This maps requests for the root page directly to the frontend files
app.use(express.static(__dirname));

// Extract the Groq API Key from environment variables
const GROQ_API_KEY = process.env.GROQ_API_KEY;

/**
 * POST /api/analyze
 * Endpoint to process user skills, interests, and goals.
 * Expects { skills: string, interests: string, goal: string } in request body.
 */
app.post("/api/analyze", async (req, res) => {
  // Destructure user input fields from the parsed request body
  const { skills, interests, goal } = req.body || {};
  
  // Validate presence of required fields; return a 400 Bad Request error if any are missing
  if (!skills || !interests || !goal) {
    return res.status(400).json({ error: "skills, interests, and goal are all required." });
  }

  try {
    // Invoke Groq API query helper to process input profiles
    const data = await callGroq(skills, interests, goal);
    // Send back the structured career roadmap as a JSON response
    return res.json(data);
  } catch (err) {
    // Send 500 Internal Server Error back to the client if the API query or parsing failed
    return res.status(500).json({ error: err.message });
  }
});

/**
 * callGroq
 * Connects to Groq API using standard fetch to generate a personalized career roadmap.
 * Instructs the LLM to output a strictly formatted JSON structure.
 * 
 * @param {string} skills User's technical and soft skills
 * @param {string} interests User's focus areas/interests
 * @param {string} goal User's target career timeline/milestone
 * @returns {Promise<object>} Parsed roadmap JSON object
 */
async function callGroq(skills, interests, goal) {
  // Construct the prompt with strict output formatting rules and schema guidelines
  // The system instructs the Llama model on formatting rules, domains, stipend details, and structure.
  const prompt = `You are NaviGen AI, an expert Career Navigation Agent for technology careers.

Analyze this user profile:
- Skills: ${skills}
- Interests: ${interests}
- Career Goal: ${goal}

Determine the BEST-FIT technology career path based on the actual profile. Do NOT default to Data Analytics unless profile strongly shows it.

Domains to consider: Web Development, Full Stack Development, AI/ML, Data Science, Data Analytics, Cybersecurity, Cloud Computing, DevOps, Blockchain, Mobile Development, UI/UX Design, Product Management, Game Development, Embedded Systems.

Return ONLY valid JSON, absolutely no markdown fences, no explanation, just raw JSON:
{
  "careerPath": "exact career domain name",
  "matchPercentage": 85,
  "careerDescription": "2-3 sentences why this path fits this person specifically",
  "skillGaps": [
    { "skill": "Skill Name", "priority": "high", "reason": "one sentence why needed" },
    { "skill": "Skill Name", "priority": "medium", "reason": "one sentence why needed" },
    { "skill": "Skill Name", "priority": "low", "reason": "one sentence why needed" }
  ],
  "learningResources": [
    { "name": "Resource Name", "platform": "Platform/URL", "free": true },
    { "name": "Resource Name", "platform": "Platform/URL", "free": true },
    { "name": "Resource Name", "platform": "Platform/URL", "free": true },
    { "name": "Resource Name", "platform": "Platform/URL", "free": false },
    { "name": "Resource Name", "platform": "Platform/URL", "free": false }
  ],
  "certifications": [
    { "name": "Full Certification Name", "provider": "Issuing Organization", "cost": "Free / $X" }
  ],
  "internships": [
    { "role": "Internship Role Title", "platform": "Platform name", "type": "Remote/On-site/Hybrid", "stipend": "Paid – ₹X,000/month" },
    { "role": "Internship Role Title", "platform": "Platform name", "type": "Remote/On-site/Hybrid", "stipend": "Unpaid – certificate + experience" },
    { "role": "Internship Role Title", "platform": "Platform name", "type": "Remote/On-site/Hybrid", "stipend": "Paid – ₹X,000/month" }
  ],
  "jobRoles": [
    { "title": "Job Title", "level": "Entry-level", "description": "what this role involves day-to-day and why it fits this exact profile" },
    { "title": "Job Title", "level": "Entry-level", "description": "..." },
    { "title": "Job Title", "level": "Mid-level (after 1-2 yrs)", "description": "..." }
  ],
  "portfolioProjects": [
    { "title": "Project Name", "difficulty": "Beginner", "description": "what to build and exactly what it proves to a recruiter", "skills": ["skill1", "skill2"] },
    { "title": "Project Name", "difficulty": "Intermediate", "description": "...", "skills": ["skill1", "skill2"] },
    { "title": "Project Name", "difficulty": "Advanced", "description": "...", "skills": ["skill1", "skill2"] }
  ],
  "salaryInsights": {
    "entry": "₹X–Y LPA",
    "mid": "₹X–Y LPA",
    "senior": "₹X–Y LPA"
  },
  "roadmap": [
    { "phase": "Phase 1 – Foundation", "duration": "4–6 weeks", "description": "detailed description", "tasks": ["task1", "task2", "task3"] },
    { "phase": "Phase 2 – Core Skills", "duration": "6–8 weeks", "description": "detailed description", "tasks": ["task1", "task2", "task3"] },
    { "phase": "Phase 3 – Build Projects", "duration": "6–8 weeks", "description": "detailed description", "tasks": ["task1", "task2", "task3"] },
    { "phase": "Phase 4 – Job Readiness", "duration": "4–6 weeks", "description": "detailed description", "tasks": ["task1", "task2", "task3"] }
  ]
}

Rules:
- learningResources: include AT LEAST 3 free resources and AT LEAST 2 paid resources. Name real platforms (YouTube channels, freeCodeCamp, Coursera, Udemy, official docs, etc.) — not generic placeholders.
- internships: include a MIX of paid and unpaid opportunities. Name real platforms (Internshala, LinkedIn, Wellfound/AngelList, Naukri, Turing, Remotive, etc.) and state the stipend honestly — don't claim every internship is paid.
- jobRoles: exactly 3 roles spanning entry-level to slightly-above, matched specifically to this profile's skills and goal.
- portfolioProjects: exactly 3 projects ordered Beginner → Intermediate → Advanced, each realistically buildable in this domain and genuinely resume-worthy.`;

  // Make direct POST request to Groq's OpenAI-compatible chat completion endpoint
  const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${GROQ_API_KEY}`,
    },
    body: JSON.stringify({
      model: "llama-3.3-70b-versatile",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.65, // Balances creativity and schema consistency
      max_tokens: 3200,  // Allocates sufficient token budget for the structured response
    }),
  });

  // Handle Rate Limiting (HTTP 429) gracefully to let client know they are sending too many requests
  if (r.status === 429) throw new Error("RATE_LIMIT");
  
  // Throw errors for any other non-OK response codes
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${r.status}`);
  }

  // Parse response body as JSON
  const json = await r.json();
  const raw = json?.choices?.[0]?.message?.content || "";
  
  // Clean potential markdown code blocks (e.g. ```json ... ```) if the model ignored the no-markdown constraint
  const clean = raw.replace(/```json|```/gi, "").trim();
  
  try {
    // Attempt standard parse of the cleaned string
    return JSON.parse(clean);
  } catch {
    // Regex fallback to extract everything within the outermost curly braces if conversational text wrapper is returned
    const m = clean.match(/\{[\s\S]*\}/);
    if (m) return JSON.parse(m[0]);
    // Fallback if parsing fails entirely
    throw new Error("AI returned invalid JSON. Please try again.");
  }
}

// Select port from environment variables (e.g. deployment environments) or default to 3000
const PORT = process.env.PORT || 3000;
// Start listening for HTTP connections on the designated port and log a message
app.listen(PORT, () => console.log(`🚀 NaviGen AI server running at http://localhost:${PORT}`));