# Study Guide Generator (7_study_guide_generator.py)

Concise README for the Study Guide Generator project.

## Overview

Generates a structured study guide for a given topic using Google's Gemini models via the `langchain-google-genai` integration. The project demonstrates single-input, tone selection, and batch processing examples using `ChatGoogleGenerativeAI` and `PromptTemplate`.

## Requirements

- Python 3.10+ (this workspace uses the `journey` virtualenv at `journey/bin/python`).
- Install required packages (either via `requirement.txt` or directly):

```bash
pip install google-generativeai langchain-core langchain-google-genai python-dotenv
```

Activate the virtualenv before running (if using the workspace venv):

```bash
source journey/bin/activate
```

## Environment

The script expects a `GOOGLE_API_KEY` environment variable (not GEMINI_API_KEY). Create a `.env` file in the project root or export the variable:

```dotenv
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Usage

Run the script from the workspace root:

```bash
python journey/7_study_guide_generator.py
```

By default the `main()` function runs three examples (single input, casual/formal tone, batch processing) using hard-coded sample texts. To make the script interactive, replace the sample strings in `main()` with `input()` calls or refactor to accept CLI arguments.

Example interactive change (replace sample assignment):

```python
input_text = input("Enter a topic or subject for the study guide: ")
```

## Example Session

Sample input:

- Topic: "Photosynthesis"
- Tone: Formal

Expected output: a multi-section study guide covering key concepts, definitions, timelines, and practice questions.

## Implementation Notes

- Uses `StudyGuideGenerator` class which internally creates `PromptTemplate` and `ChatPromptTemplate` instances.
- The generator creates LCEL-style chains by piping the prompt template into `ChatGoogleGenerativeAI` and `StrOutputParser`.
- The default examples in `main()` are hard-coded; the script does not prompt the user interactively unless you change those lines.

## Troubleshooting

- If the script does nothing interactive, edit `main()` and replace the hard-coded `input_text` and `texts` with `input()` or CLI parsing.
- Missing API key: ensure `GOOGLE_API_KEY` is set and `load_dotenv()` can read `.env`.
- Import errors for `langchain_google_genai`: ensure you are using the workspace virtualenv and run `pip show langchain-google-genai` to confirm installation.
- If the LLM returns structured objects, use `.text` on returned messages or use `StrOutputParser()` to extract raw text.

## Next steps / Improvements

- Add an `argparse`-based CLI for non-interactive usage and batch input files.
- Add unit tests and CI for prompt templates and parsing logic.
- Add better error handling and retry/backoff for API calls.

---

File: journey/7_study_guide_generator.py
