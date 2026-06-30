# Email Generator (6_Email_Generator.py)

A concise README for the `6_Email_Generator.py` script.

## Overview

Generates professional email subject lines and body text using Google's Gemini models via the `langchain-google-genai` integration. The script is interactive and produces subject + body variants in configurable tones.

## Requirements

- Python 3.10+ (this workspace uses Python 3.14 virtualenv at `journey/bin/python`).
- Install dependencies listed in `requirement.txt` or install the main packages:

```bash
pip install google-generativeai langchain-core langchain-google-genai python-dotenv
```

If you use the repository virtualenv, activate it first:

```bash
source journey/bin/activate
```

## Environment

Create a `.env` file in the project root (or export env var) with your Gemini API key:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
```

The script checks for `GEMINI_API_KEY` at runtime and will raise a ValueError if it's missing.

## Usage

Run the script from the workspace root (with the virtualenv active when applicable):

```bash
python journey/6_Email_Generator.py
```

The script will prompt for:
- recipient's name
- purpose (meeting request, follow-up, complaint, etc.)
- tone (formal, friendly, assertive)
- additional context

It then prints the generated subject and body content.

## Example Session

Inputs:

- Recipient: Sarah
- Purpose: Meeting Request
- Tone: Formal
- Context: Discuss project timeline and deliverables

Sample output (subject + body):

```
Subject: Request for Meeting — Project Timeline Discussion

Body:
Dear Sarah,

I hope you are well. I would like to schedule a meeting to review the project timeline and upcoming deliverables. Please let me know your availability next week...
```

## Implementation notes

- The script uses `PromptTemplate` to create separate prompts for the subject and body.
- It uses `ChatGoogleGenerativeAI` from `langchain_google_genai` as the LLM wrapper and `StrOutputParser` to get plain text output.
- If you see import errors like `cannot import name 'GoogleGenAI'`, ensure you're importing the correct classes: this package exposes `ChatGoogleGenerativeAI` and `GoogleGenerativeAI` (not `GoogleGenAI`).
- Keep `langchain-google-genai` and `langchain-core` versions compatible — use recent releases.

## Troubleshooting

- Missing `GEMINI_API_KEY`: create `.env` or set the env var.
- ImportError for `langchain_google_genai`: verify the virtualenv and installed package versions: `pip show langchain-google-genai`.
- If the model returns structured response objects, use `StrOutputParser()` (already used in the script) or access `.text` on returned messages.

## Next steps / Improvements

- Add CLI flags for non-interactive usage (`argparse`).
- Add unit tests for prompt formatting and output parsing.
- Add retries and better error handling for API calls.

---

File: journey/6_Email_Generator.py
