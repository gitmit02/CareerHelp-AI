"""
CareerHelpAI — Minimal MCP Server (Kaggle Capstone demo)
==========================================================
Exposes exactly two tools over the Model Context Protocol:
  1. search_courses(skill)        -> static demo course list
  2. internship_platforms(domain) -> static demo platform list

Standalone. Does not import, modify, or depend on anything else in the
CareerHelpAI project (no server.js, no ADK agent, no frontend).
"""

# Import FastMCP class from mcp SDK to initialize our Model Context Protocol server instance
from mcp.server.fastmcp import FastMCP

# Instantiate FastMCP server under a specific workspace identifier
mcp = FastMCP("CareerHelpAI-MCP")

# Static demo data — no database, no network calls.
# COURSE_DATA stores course recommendations indexed by lowercased skill keywords
COURSE_DATA = {
    "react": [
        {"title": "React Course", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/"},
        {"title": "React - The Complete Guide", "platform": "Udemy", "url": "https://www.udemy.com/"},
        {"title": "React Docs", "platform": "react.dev", "url": "https://react.dev/"},
    ],
    "python": [
        {"title": "Python for Everybody", "platform": "Coursera", "url": "https://www.coursera.org/"},
        {"title": "Python Full Course", "platform": "freeCodeCamp", "url": "https://www.freecodecamp.org/"},
    ],
    "machine learning": [
        {"title": "Machine Learning Crash Course", "platform": "Google Developers", "url": "https://developers.google.com/machine-learning/crash-course"},
        {"title": "Deep Learning Specialization", "platform": "Coursera", "url": "https://www.coursera.org/"},
    ],
}

# PLATFORM_DATA stores internship platform name suggestions mapped by career field domain keywords
PLATFORM_DATA = {
    "ai/ml": ["Internshala", "LinkedIn Jobs", "Google Careers", "Wellfound"],
    "web development": ["Internshala", "LinkedIn Jobs", "AngelList", "Naukri"],
    "data science": ["Internshala", "LinkedIn Jobs", "Kaggle Jobs", "Wellfound"],
}

# DEFAULT_COURSES lists fallback resources when a searched skill keyword is not found in COURSE_DATA
DEFAULT_COURSES = [
    {"title": f"{{skill}} Fundamentals", "platform": "Coursera", "url": "https://www.coursera.org/"},
]
# DEFAULT_PLATFORMS lists fallback platforms when domain keyword does not exist in PLATFORM_DATA
DEFAULT_PLATFORMS = ["Internshala", "LinkedIn Jobs", "Wellfound"]


# Use FastMCP tool decorator to register search_courses as a callable capability of the MCP server
@mcp.tool()
def search_courses(skill: str) -> dict:
    """Search for online courses related to a given skill.

    Args:
        skill: The skill to search courses for, e.g. "React".

    Returns:
        dict with a "courses" list of {title, platform, url}.
    """
    # Clean the input query by stripping whitespace and lowercasing
    key = skill.strip().lower()
    # Query static COURSE_DATA dictionary
    courses = COURSE_DATA.get(key)
    # Check if courses are found; fallback to default courses list if not
    if not courses:
        courses = [{"title": f"{skill} Fundamentals", "platform": "Coursera", "url": "https://www.coursera.org/"}]
    return {"courses": courses}


# Register internship_platforms as a tool on our MCP instance
@mcp.tool()
def internship_platforms(domain: str) -> dict:
    """List internship platforms relevant to a given career domain.

    Args:
        domain: The career domain, e.g. "AI/ML".

    Returns:
        dict with a "platforms" list of platform names.
    """
    # Clean the domain key query parameter
    key = domain.strip().lower()
    # Match against PLATFORM_DATA dataset, fallback to DEFAULT_PLATFORMS if key doesn't match
    platforms = PLATFORM_DATA.get(key, DEFAULT_PLATFORMS)
    return {"platforms": platforms}


# Launch the MCP server over standard input/output transport when executed directly
if __name__ == "__main__":
    mcp.run()