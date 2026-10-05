---
description: Commit, push, PR, merge, and clean up the current feature branch
allowed-tools: Read, Glob, Bash(git:*), Bash(gh:*)
---

You are an AI agent shipping the current feature for the Graana
Market Intelligence project. Follow all rules in @AGENTS.md.

## Global rules
- If ANY step fails, stop immediately, report the error, and do not
  continue to the next step.
- Never commit directly to `main`.
- Never use `git add .` or `git add -A`. Stage files explicitly.
- Never stage `.env`, secrets, credentials, or unrelated scratch files.
- Never tick a checklist item you have not verified.
- Wait for the user's explicit reply at every "CHECKPOINT". Do not
  assume approval.
- If `gh` is not authenticated, stop and say:
  "GitHub CLI is not authenticated. Run `gh auth login`."

## Step 1 — Identify branch and state
```bash
git branch --show-current
git status --short
```
Store the branch as CURRENT_BRANCH.

- If the branch is empty (detached HEAD) or is `main`, refuse to
  continue.
- If there is nothing to commit AND `git log main..HEAD --oneline`
  is empty, stop and say: "Nothing to ship on this branch."

## Step 2 — Find the spec
Read `.opencode/specs/` and find the spec matching the current
feature (match on branch name or step number).

- If no spec matches, or several could match, list the candidates
  and ask the user which one to use. Wait for the reply.

## Step 3 — Verify the work
Read the spec's Definition of done and any test/run instructions.
Run the checks that can be run (for example `uv run pytest`, linting,
type checks, or the commands in the spec's test section).

- Record each Definition of done item as PASSED, FAILED, or NOT
  VERIFIED.
- If any check FAILED, stop and report. Do not ship.

## Step 4 — Generate commit message
```bash
git status --short
git diff
git diff --staged
git log main..HEAD --oneline
```
Remember that `git diff` does not show untracked files; use the
`git status` output to account for them.

Generate a Conventional Commit message:
- feat: new feature
- fix: bug fix
- chore: config or tooling
- docs: documentation only

Rules:
- Lowercase
- No period at the end
- Under 72 characters
- Describes what the user can now do, not what the code does

Good: "feat: add scraper retries with tenacity backoff"
Bad: "feat: added tenacity to main.py"

### CHECKPOINT 1
Show the user:
- the exact list of files you intend to stage
- any files you are deliberately leaving out, and why
- the proposed commit message
- the Definition of done results from Step 3

Ask: "Commit and push these? (yes / edit / cancel)"
Stop and wait for the reply.

## Step 5 — Commit
Stage only the approved files by name:
```bash
git add <file1> <file2> ...
git commit -m "<generated-message>"
```
Report: "✓ Committed — <message>"

## Step 6 — Push to feature branch
```bash
git push -u origin CURRENT_BRANCH
```
Report: "✓ Pushed — CURRENT_BRANCH"

## Step 7 — Create PR
Write the PR body to a temporary file (for example
`.opencode/tmp/pr-body.md`) using the Write tool, then create the PR
with `--body-file`. This avoids quoting problems with backticks and
multi-line markdown.

```bash
gh pr create --title "<plain English feature name>" --body-file .opencode/tmp/pr-body.md
```
Title: plain English feature name, no conventional commit prefix.

Body template:
```markdown
## What this PR does
<one paragraph from the spec overview section>

## Changes
<bullet list of every file changed with one line description each>

## Definition of done
<copy the checklist from the spec; mark [x] ONLY for items marked
PASSED in Step 3, leave the rest as [ ] and note why>

## How to test
1. <setup steps, e.g. uv run python main.py>
2. <specific steps from the spec to verify this feature works>
```

After creating the PR, delete the temporary body file.
Report: "✓ PR created — <PR URL>"

If PR creation fails, stop. Never proceed to merge.

## Step 8 — Wait for checks
```bash
gh pr checks --watch
```
- If the repo has no checks configured, note that and continue.
- If any check fails, stop and report. Do not merge.

### CHECKPOINT 2
Ask: "PR is ready: <PR URL>. Squash merge to main and clean up
branches? (yes / cancel)"
Stop and wait for the reply.

## Step 9 — Merge PR
```bash
gh pr merge --squash --delete-branch
```
Then verify the merge actually happened:
```bash
gh pr view --json state -q .state
```
The result must be `MERGED`. If not, stop and report.
Report: "✓ PR merged to main"

## Step 10 — Switch to main and pull
```bash
git checkout main
git pull origin main
```
Report: "✓ Switched to main — up to date"

## Step 11 — Clean up branches
`gh pr merge --delete-branch` removes the remote branch. Confirm:
```bash
git ls-remote --heads origin CURRENT_BRANCH
```
If it still exists, delete it:
```bash
git push origin --delete CURRENT_BRANCH
```
Report: "✓ Remote branch deleted"

Because the PR was squash merged, git will not see the local branch
as merged, so `-D` is required. Only run it now that Step 9 confirmed
the state is `MERGED`:
```bash
git branch -D CURRENT_BRANCH
```
Report: "✓ Local branch deleted"

## Final summary
Print:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
/ship-feature complete
✓ Verified — <n> checks passed
✓ Committed — <message>
✓ Pushed — <branch>
✓ PR created and merged
✓ Remote branch deleted
✓ Switched to main
✓ Local branch deleted
Next: run /create-spec for the next feature
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
