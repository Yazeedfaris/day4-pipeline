"""Lab 4.1 — PR review agent, run by GitHub Actions on every pull request.
Generates a review summary, flags missing tests, posts a PR comment,
and invites reviewer feedback (reactions are the feedback log).
"""
import json, os, subprocess, urllib.request
from openai import OpenAI

client = OpenAI(base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"])
MODEL = os.environ.get("REVIEW_MODEL", "openai/gpt-4o-mini")

base, head = os.environ["BASE_SHA"], os.environ["HEAD_SHA"]
diff = subprocess.run(["git", "diff", f"{base}...{head}", "--unified=3"],
                      capture_output=True, text=True).stdout[:60000]
names = subprocess.run(["git", "diff", "--name-only", f"{base}...{head}"],
                       capture_output=True, text=True).stdout.split()

code_changed = [f for f in names
                if f.endswith(".py") and "test" not in os.path.basename(f)]
tests_changed = [f for f in names if "test" in os.path.basename(f)]
missing_tests = bool(code_changed) and not tests_changed

r = client.chat.completions.create(model=MODEL, messages=[
    {"role": "system", "content":
     "You are a code review agent. Review the diff for correctness, "
     "style and risk. Be specific and brief. Return STRICT JSON: "
     '{"summary": "...", "risks": ["..."], "suggestions": ["..."]}'},
    {"role": "user", "content": f"Changed files: {names}\n\nDIFF:\n{diff}"}])
txt = r.choices[0].message.content.strip()
txt = txt.removeprefix("```json").removeprefix("```").removesuffix("```")
review = json.loads(txt)

flag = ("\n\n> **Missing tests:** code files changed but no test files "
        "were updated.") if missing_tests else ""
risks = review.get("risks") or ["none noted"]
sugg = review.get("suggestions") or ["none"]
body = (f"## Agent Review\n\n{review.get('summary', '')}\n\n### Risks\n"
        + "\n".join(f"- {x}" for x in risks)
        + "\n\n### Suggestions\n" + "\n".join(f"- {x}" for x in sugg)
        + flag
        + "\n\n*Feedback: react \U0001F44D/\U0001F44E to this comment — "
          "reactions are our improvement log.*")

req = urllib.request.Request(
    "https://api.github.com/repos/{}/issues/{}/comments".format(
        os.environ["REPO"], os.environ["PR_NUMBER"]),
    data=json.dumps({"body": body}).encode(),
    headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
             "Accept": "application/vnd.github+json",
             "Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print("comment posted, HTTP", resp.status)
