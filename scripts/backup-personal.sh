#!/usr/bin/env bash
# Career OS — Personal Data Backup
# Commits personal data files to the personal-data branch and pushes to personal remote.
# Safe to run from main at any time — uses a worktree, never switches branches.
# Usage: bash scripts/backup-personal.sh

set -e

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
WORKTREE="$REPO_ROOT/.personal-worktree"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"

# Ensure worktree exists
if [ ! -d "$WORKTREE" ]; then
  echo "Setting up personal-data worktree..."
  git -C "$REPO_ROOT" worktree add "$WORKTREE" personal-data
fi

# Personal data paths to sync (relative to repo root)
PERSONAL_PATHS=(
  "checkpoints"
  "data"
  "resumes"
  "config/user.json"
)

echo "Syncing personal data to .personal-worktree..."

for path in "${PERSONAL_PATHS[@]}"; do
  src="$REPO_ROOT/$path"
  dst="$WORKTREE/$path"

  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -r "$src" "$(dirname "$dst")/"
  fi
done

# Commit and push from worktree
cd "$WORKTREE"

git add -A

if git diff --cached --quiet; then
  echo "Nothing changed — personal data already up to date."
else
  git commit -m "backup: personal data — $TIMESTAMP"
  git push personal-data-remote personal-data 2>/dev/null || \
  git push git@github-career-os:shubhamcodess/career-os-sp.git personal-data
  echo "✓ Personal data backed up to career-os-sp:personal-data"
fi

cd "$REPO_ROOT"
