#!/usr/bin/env bash
# Career OS — Vault Sync
#
# Pushes personal data to your private backup repo (career-os-private).
# Run after every intake session, resume generation, or job tracker update.
#
# Requires PRIVATE_REPO_URL in .env  (e.g. git@github.com:you/career-os-private.git)
# Uses a local branch "personal-main" checked out in .personal-worktree.
# Safe to run anytime — never switches your working tree or touches local main.
#
# Usage: bash scripts/sync-vault.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

# ── Load .env ────────────────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

if [ -z "$PRIVATE_REPO_URL" ]; then
  echo "❌  PRIVATE_REPO_URL is not set in .env"
  echo "    Add: PRIVATE_REPO_URL=git@github.com:yourusername/career-os-private.git"
  exit 1
fi

if [ "${PERSONALIZE:-false}" != "true" ]; then
  echo "ℹ️   PERSONALIZE is not set to true in .env — nothing to sync."
  echo "    Set PERSONALIZE=true to enable personal data tracking."
  exit 0
fi

WORKTREE="$REPO_ROOT/.personal-worktree"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"

# ── Ensure personal-main branch exists ───────────────────────────────────────
if ! git -C "$REPO_ROOT" show-ref --quiet refs/heads/personal-main; then
  echo "Creating personal-main branch from main..."
  git -C "$REPO_ROOT" branch personal-main main
fi

# ── Ensure worktree is set up ─────────────────────────────────────────────────
if [ ! -d "$WORKTREE" ]; then
  echo "Setting up personal-main worktree..."
  git -C "$REPO_ROOT" worktree add "$WORKTREE" personal-main
fi

cd "$WORKTREE"

# ── Bring in latest framework commits from main ───────────────────────────────
git merge main --no-edit -m "merge: framework from main — $TIMESTAMP" 2>/dev/null || true

# ── Copy personal data files into worktree ────────────────────────────────────
PERSONAL_PATHS=("checkpoints" "data" "resumes" "config/user.json")
for path in "${PERSONAL_PATHS[@]}"; do
  src="$REPO_ROOT/$path"
  dst_dir="$(dirname "$WORKTREE/$path")"
  if [ -e "$src" ]; then
    mkdir -p "$dst_dir"
    cp -r "$src" "$dst_dir/"
  fi
done

# ── Stage everything (force-add gitignored personal files) ────────────────────
git add -A
git add -f checkpoints data resumes config/user.json 2>/dev/null || true

if git diff --cached --quiet; then
  echo "Nothing changed — vault already up to date."
else
  git commit -m "sync: personal data — $TIMESTAMP"
  echo "✓ Committed personal data snapshot."
fi

# ── Push to private repo ──────────────────────────────────────────────────────
git push "$PRIVATE_REPO_URL" personal-main:main
echo "✓ Vault synced → $PRIVATE_REPO_URL (main)"

cd "$REPO_ROOT"
