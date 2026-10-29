
"""Lab 4.1 — PR review agent.

Runs in GitHub Actions on pull requests.
Generates an AI review, flags missing tests,
and posts the review as a PR comment.
"""

import json
import os
import subprocess
import urllib.request

from openai import OpenAI


# 1. Connect to OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = os.environ.get(
    "REVIEW_MODEL", "openai/gpt-4o-mini"
)


# 2. Read changes between the two branches
base = os.environ["BASE_SHA"]
head = os.environ["HEAD_SHA"]

diff = subprocess.run(
    ["git", "diff", f"{base}...{head}", "--unified=3"],
    capture_output=True,
    text=True,
    check=True,
).stdout[:60000]

names = subprocess.run(
    ["git", "diff", "--name-only", f"{base}...{head}"],
    capture_output=True,
    text=True,
    check=True,
).stdout.split()


# 3. Detect missing tests
code_changed = [
    f for f in names
    if f.endswith(".py")
    and "test" not in os.path.basename(f)
]

tests_changed = [
    f for f in names
    if "test" in os.path.basename(f)
]

missing_tests = bool(code_changed) and not tests_changed


# 4. Ask the AI model to review the changes
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a code review agent. "
                "Review the diff for correctness, style, and risk. "
                "Be specific and brief. "
                "Return STRICT JSON: "
                '{"summary": "...", '
                '"risks": ["..."], '
                '"suggestions": ["..."]}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Changed files: {names}\n\n"
                f"DIFF:\n{diff}"
            ),
        },
    ],
)


# 5. Validate and parse the model response
content = response.choices[0].message.content
txt = (content or "").strip()

if not txt:
    raise RuntimeError(
        "Model returned empty content. "
        f"Finish reason: {response.choices[0].finish_reason}"
    )

txt = (
    txt.removeprefix("```json")
    .removeprefix("```")
    .removesuffix("```")
    .strip()
)

try:
    review = json.loads(txt)
except json.JSONDecodeError as exc:
    raise RuntimeError(
        "Model returned invalid JSON. "
        f"Response length: {len(txt)} characters. "
        f"JSON error: {exc}"
    ) from exc

if not isinstance(review, dict):
    raise RuntimeError(
        "Model response must be a JSON object."
    )

if (
    not isinstance(review.get("summary"), str)
    or not isinstance(review.get("risks"), list)
    or not isinstance(review.get("suggestions"), list)
    or not all(
        isinstance(item, str)
        for item in review["risks"] + review["suggestions"]
    )
):
    raise RuntimeError(
        "Model response does not match the expected review schema."
    )


# 6. Build the review comment
flag = (
    "\n\n> **Missing tests:** "
    "code files changed but no test files were updated."
    if missing_tests
    else ""
)

risks = review["risks"] or ["none noted"]
suggestions = review["suggestions"] or ["none"]

body = (
    f"## Agent Review\n\n{review['summary']}\n\n"
    "### Risks\n"
    + "\n".join(f"- {item}" for item in risks)
    + "\n\n### Suggestions\n"
    + "\n".join(f"- {item}" for item in suggestions)
    + flag
    + "\n\n*Feedback: react good/bad to this comment — "
      "reactions are our improvement log.*"
)


# 7. Post the review to GitHub
repo = os.environ["REPO"]
pr_number = os.environ["PR_NUMBER"]

url = (
    f"https://api.github.com/repos/"
    f"{repo}/issues/{pr_number}/comments"
)

request = urllib.request.Request(
    url,
    data=json.dumps({"body": body}).encode("utf-8"),
    headers={
        "Authorization": (
            "Bearer " + os.environ["GITHUB_TOKEN"]
        ),
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as result:
    print("Review comment posted, HTTP", result.status)
