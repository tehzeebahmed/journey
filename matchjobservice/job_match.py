"""
Job Match Analyzer - Resume vs JD matcher using Mistral AI
Usage: python3 job_match.py <job_url>
Requires: pip install mistralai requests beautifulsoup4 --break-system-packages
Set env var: MISTRAL_API_KEY
"""

import os
import sys
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from mistralai.client import Mistral

MISTRAL_MODEL = "mistral-small-latest"

RESUME_TEXT = """Tehzeeb Ahmed
Sr Data Architect – Cloud and enterprise data platform
[... full resume text loaded from file at runtime ...]
"""

RESUME_PATH = os.path.join(os.path.dirname(__file__), "resume.txt")


def load_resume():
    with open(RESUME_PATH, "r") as f:
        return f.read()


def fetch_jd_text(url):
    """Fetch and extract visible text from a job posting URL."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)

    print("---- RAW EXTRACTED JD TEXT (first 2000 chars) ----")
    print(cleaned[:2000])
    print("---- END PREVIEW ----\n")

    return cleaned


def build_prompt(resume_text, jd_text):
    return f"""You are an expert technical recruiter and career coach.

Below is a candidate's RESUME and a JOB DESCRIPTION (raw scraped text, may contain
navigation noise - ignore irrelevant boilerplate).

Analyze the match and respond ONLY in valid JSON with this exact structure:

{{
  "match_percentage": <integer 0-100>,
  "verdict": "<one of: 'Strong Apply', 'Apply with tailoring', 'Apply as stretch role', 'Do not apply'>",
  "key_matching_strengths": ["...", "..."],
  "key_gaps": ["...", "..."],
  "ats_keywords_missing": ["...", "..."],
  "resume_tailoring_suggestions": [
    {{"section": "Professional Summary", "suggestion": "..."}},
    {{"section": "Core Competencies", "suggestion": "..."}},
    {{"section": "Key Achievements", "suggestion": "..."}}
  ],
  "tailored_summary_rewrite": "<2-3 sentence rewritten professional summary tailored to this JD>",
  "overall_reasoning": "<short paragraph explaining the score>"
}}

RESUME:
{resume_text}

JOB DESCRIPTION (raw text):
{jd_text[:8000]}
"""


def call_mistral(prompt):
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: Set MISTRAL_API_KEY environment variable.")
        sys.exit(1)

    client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content

    print("---- RAW MISTRAL RESPONSE ----")
    print(raw)
    print("---- USAGE ----")
    print(response.usage)
    print("---- END ----\n")

    return raw


def print_report(data):
    print("=" * 60)
    print(f"MATCH PERCENTAGE: {data.get('match_percentage')}%")
    print(f"VERDICT: {data.get('verdict')}")
    print("=" * 60)

    print("\nKEY MATCHING STRENGTHS:")
    for s in data.get("key_matching_strengths", []):
        print(f"  + {s}")

    print("\nKEY GAPS:")
    for g in data.get("key_gaps", []):
        print(f"  - {g}")

    print("\nMISSING ATS KEYWORDS TO ADD:")
    for k in data.get("ats_keywords_missing", []):
        print(f"  * {k}")

    print("\nRESUME TAILORING SUGGESTIONS:")
    for sug in data.get("resume_tailoring_suggestions", []):
        print(f"  [{sug.get('section')}] -> {sug.get('suggestion')}")

    print("\nTAILORED SUMMARY REWRITE:")
    print(f"  {data.get('tailored_summary_rewrite')}")

    print("\nREASONING:")
    print(f"  {data.get('overall_reasoning')}")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 job_match.py <job_url>")
        sys.exit(1)

    url = sys.argv[1]

    print(f"[1/4] Loading resume from {RESUME_PATH} ...")
    resume_text = load_resume()
    print(f"      Loaded {len(resume_text)} chars.\n")

    print(f"[2/4] Fetching JD from URL: {url}")
    jd_text = fetch_jd_text(url)
    print(f"      Extracted {len(jd_text)} chars.\n")

    print("[3/4] Building prompt and calling Mistral...")
    prompt = build_prompt(resume_text, jd_text)
    raw_response = call_mistral(prompt)

    print("[4/4] Parsing JSON response...")
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"FAILED to parse JSON: {e}")
        print("Raw output above - inspect manually.")
        sys.exit(1)

    print_report(data)

    out_file = f"last_match_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nFull report saved to {out_file}")


if __name__ == "__main__":
    main()
