#!/usr/bin/env bash
# One-time GitHub browser login for git + Git LFS (HTTPS).
# Run from Terminal.app (not headless): ./scripts/github-browser-auth.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "→ GitHub browser authentication (HTTPS)"
echo "  A browser window will open — sign in as fornevercollective"
echo ""

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh"
  exit 1
fi

gh auth login \
  --hostname github.com \
  --git-protocol https \
  --web \
  --scopes repo,workflow,read:org,gist

gh auth setup-git
gh config set git_protocol https

git remote set-url origin https://github.com/fornevercollective/codex-regius-digital.git

echo ""
echo "✓ Credentials configured. Testing push access..."
GIT_TERMINAL_PROMPT=0 git ls-remote origin HEAD >/dev/null
echo "✓ Remote OK: $(git remote get-url origin)"
echo ""
echo "Push from GitHub Desktop or run: git push origin main"