---
name: github-workflows
description: "GitHub operations: auth, PR lifecycle, issues, repos, releases, code review, codebase inspection. One umbrella for all GitHub-related git/gh/curl workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, PR, Issues, Authentication, CI/CD, Code-Review, Repositories]
    related_skills: []
---

# GitHub Workflows

Complete guide for all GitHub-related operations — authentication, pull requests, issues,
repository management, code review, releases, CI/CD, and codebase inspection. Each section
shows `gh` first, then `git` + `curl` fallback for machines without `gh`.

This umbrella skill consolidates 6 sibling skills. The detailed per-operation guides are
now subsections below. New work should start here and drill into subsections as needed.

## Quick reference

| Operation | Guide | CLI shortcut |
|-----------|-------|-------------|
| Auth setup | § Authentication | `gh auth login` or PAT |
| Create PR | § Pull Request Lifecycle | `gh pr create` |
| Review PR | § Code Review | `gh pr review N` |
| Manage issues | § Issues | `gh issue create` |
| Manage repos | § Repository Management | `gh repo create` |
| CI/CD | § Repository Management → Actions | `gh run list` |
| Codebase sizing | § Codebase Inspection | `pygount --format=summary` |
| Releases | § Repository Management → Releases | `gh release create` |

## Table of Contents

1. [Authentication Setup](/skills/github/github-auth/SKILL.md)
2. [Pull Request Lifecycle](/skills/github/github-pr-workflow/SKILL.md)
3. [Code Review](/skills/github/github-code-review/SKILL.md)
4. [Issues Management](/skills/github/github-issues/SKILL.md)
5. [Repository Management](/skills/github/github-repo-management/SKILL.md)
6. [Codebase Inspection](/skills/github/codebase-inspection/SKILL.md)

---

## § 1 — Authentication Setup

Three ways to authenticate with GitHub, depending on what's available.

### Detection Flow

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
```

**Decision tree:**
1. `gh auth status` → authenticated → use `gh` for everything
2. `gh` installed, not authenticated → `gh auth login --with-token`
3. `gh` not installed → use `git`-only methods

### Git-Only: Personal Access Token

Create a token at https://github.com/settings/tokens with `repo` and `workflow` scopes.

```bash
# Store credentials
git config --global credential.helper store

# Set identity
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Test (token is the password)
git ls-remote https://github.com/owner/repo.git
```

### Git-Only: SSH Key

```bash
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# Add to https://github.com/settings/keys
ssh -T git@github.com
```

### gh CLI

```bash
# Token-based (headless)
echo "TOKEN" | gh auth login --with-token
gh auth setup-git

# Browser-based
gh auth login
```

### Helper: Detect Auth Method

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
  REMOTE_URL=$(git remote get-url origin)
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\\.com[:/]||; s|\\.git$||')
  OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
  REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
  GH_USER=$(gh api user --jq '.login')
else
  AUTH="curl"
  # Extract token from credentials
  if [ -z "$GITHUB_TOKEN" ]; then
    [ -f "${HERMES_HOME:-~/.hermes}/.env" ] && GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "${HERMES_HOME:-~/.hermes}/.env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    [ -z "$GITHUB_TOKEN" ] && GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  fi
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use PAT as password, or switch to SSH |
| `remote: Permission denied` | Token lacks `repo` scope |
| `fatal: Authentication failed` | Stale credentials — `git credential reject` then re-auth |
| `ssh: connect to host github.com port 22 refused` | Use SSH over HTTPS port 443 |

Full setup guide: see [`/skills/github/github-auth/SKILL.md`](/skills/github/github-auth/SKILL.md).

---

## § 2 — Pull Request Lifecycle

### Branch creation

```bash
git checkout main && git pull origin main
git checkout -b feat/description
```

Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `ci/`

### Making commits

```bash
git add <files>
git commit -m "type(scope): description"
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

### Push and create PR

```bash
git push -u origin HEAD

# With gh:
gh pr create --title "feat: ..." --body "## Summary\n..." --label "enhancement"

# With curl:
BRANCH=$(git branch --show-current)
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{\"title\":\"...\",\"body\":\"...\",\"head\":\"$BRANCH\",\"base\":\"main\"}"
```

### CI monitoring

```bash
# gh
gh pr checks
gh pr checks --watch

# curl
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs
```

### Auto-fix CI loop

1. Check CI status
2. Read failure logs (`gh run view <ID> --log-failed`)
3. Fix the code
4. `git add && git commit -m "fix: ..." && git push`
5. Wait and re-check (up to 3 attempts)

### Merging

```bash
gh pr merge --squash --delete-branch
# or with auto-merge:
gh pr merge --auto --squash

# curl:
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{\"merge_method\":\"squash\"}"
```

Full guide: see [`/skills/github/github-pr-workflow/SKILL.md`](/skills/github/github-pr-workflow/SKILL.md).

---

## § 3 — Code Review

Review local changes (pre-push) or open PRs on GitHub.

### Local diff review

```bash
git diff main...HEAD --stat           # scope
git diff main...HEAD                  # full diff
git diff main...HEAD -- src/file.py   # single file
```

### Review checklist

- **Correctness:** Edge cases, error paths
- **Security:** No hardcoded secrets, SQL injection, XSS, path traversal
- **Quality:** Clear naming, no duplication, single responsibility
- **Testing:** New paths covered, happy + error paths
- **Performance:** No N+1 queries, no blocking in async paths
- **Documentation:** Public APIs documented, README updated

### Posting PR review

```bash
# gh
gh pr review $PR_NUMBER --approve --body "LGTM"
gh pr review $PR_NUMBER --request-changes --body "See inline comments"

# curl — atomic review with inline comments
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d "{\"commit_id\":\"$HEAD_SHA\",\"event\":\"COMMENT\",\"body\":\"...\",\"comments\":[...]}"
```

Full guide: see [`/skills/github/github-code-review/SKILL.md`](/skills/github/github-code-review/SKILL.md).

---

## § 4 — Issues Management

### Create an issue

```bash
# gh
gh issue create --title "Bug: login redirect" --body "## Description\n..." --label "bug"

# curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title":"Bug: ...","body":"## Description","labels":["bug"]}'
```

### List, manage, triage

```bash
gh issue list --label "needs-triage"
gh issue view 42
gh issue edit 42 --add-label "priority:high"
gh issue edit 42 --add-assignee username
gh issue close 42

# curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?labels=bug"
```

### Templates

Bug report template: `title`, `description`, `steps to reproduce`, `expected vs actual`, `environment`
Feature request: `description`, `motivation`, `proposed solution`, `alternatives`

Full guide: see [`/skills/github/github-issues/SKILL.md`](/skills/github/github-issues/SKILL.md).

---

## § 5 — Repository Management

### Clone

```bash
git clone https://github.com/owner/repo.git
git clone --depth 1 https://github.com/owner/repo.git  # shallow, faster
```

### Create

```bash
# gh
gh repo create my-project --public --clone
gh repo create my-project --template owner/template-repo --public --clone

# curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","private":false,"auto_init":true}'
```

### Fork

```bash
gh repo fork owner/repo --clone
# keep in sync:
git fetch upstream && git merge upstream/main && git push origin main
```

### Settings

```bash
gh repo edit --description "..." --visibility public
gh repo edit --enable-wiki=false --add-topic "python,ml"
# Branch protection
curl -X PUT .../branches/main/protection -d '{"required_status_checks":{...}}'
```

### Secrets (GitHub Actions)

```bash
# gh (simpler)
gh secret set API_KEY --body "value"

# curl requires public-key encryption (complex — prefer gh)
```

### Releases

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
```

### Actions

```bash
gh workflow list
gh run list --limit 10
gh run view <ID> --log-failed
gh run rerun <ID>
gh workflow run ci.yml --ref main
```

### Gists

```bash
gh gist create script.py --public --desc "Useful script"
```

Full guide: see [`/skills/github/github-repo-management/SKILL.md`](/skills/github/github-repo-management/SKILL.md).

---

## § 6 — Codebase Inspection

Analyze repositories for lines of code, language breakdown, and code-vs-comment ratios using `pygount`.

### Quick start

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
pygount --format=summary --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build" .
```

### Filter by language

```bash
pygount --suffix=py --format=summary .
pygount --suffix=py,yaml,yml --format=summary .
```

### Output formats

```bash
pygount --format=summary .   # human-readable table
pygount --format=json .      # programmatic
```

### Pitfalls

- Always exclude `.git`, `node_modules`, `venv` — otherwise minutes/hang
- Markdown shows 0 code lines (all content classified as comments)
- JSON files show low code counts

Full guide: see [`/skills/github/codebase-inspection/SKILL.md`](/skills/github/codebase-inspection/SKILL.md).
