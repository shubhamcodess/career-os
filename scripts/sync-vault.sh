#!/usr/bin/env bash
# Career OS — Vault Sync
#
# Backs up personal data to your private GitHub repo.
# Run after every intake session, resume generation, or job tracker update.
#
# Usage:
#   bash scripts/sync-vault.sh                          # auto timestamp commit
#   bash scripts/sync-vault.sh -m "intake: CP-03 — …"  # Claude passes a meaningful message
#
# Requires in .env:
#   PERSONALIZE=true
#   PRIVATE_REPO_URL=git@github.com:yourusername/career-os-private.git
#
# Safe to run anytime — uses a worktree, never switches your working tree or touches main.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"
COMMIT_MSG="sync: personal data — $TIMESTAMP"

# ── Parse -m flag ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message) COMMIT_MSG="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# ── Load .env ─────────────────────────────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

if [ "${PERSONALIZE:-false}" != "true" ]; then
  echo "ℹ️   PERSONALIZE is not true in .env — nothing to sync."
  echo "    Set PERSONALIZE=true to enable personal data backup."
  exit 0
fi

if [ -z "$PRIVATE_REPO_URL" ]; then
  echo "❌  PRIVATE_REPO_URL is not set in .env"
  echo "    Add: PRIVATE_REPO_URL=git@github.com:yourusername/career-os-private.git"
  exit 1
fi

WORKTREE="$REPO_ROOT/.personal-worktree"

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
  git commit -m "$COMMIT_MSG

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
  echo "✓ Committed: $COMMIT_MSG"
fi

# ── Push to private repo ──────────────────────────────────────────────────────
git push "$PRIVATE_REPO_URL" personal-main:main
echo "✓ Vault synced → $PRIVATE_REPO_URL"

cd "$REPO_ROOT"
