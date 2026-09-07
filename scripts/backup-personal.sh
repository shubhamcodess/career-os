#!/usr/bin/env bash
# Career OS — Personal Data Backup
#
# Syncs personal data to career-os-sp:main (private repo) which has ALL files.
# The personal-main branch (in .personal-worktree) tracks personal:main.
# Safe to run from main at any time — uses a worktree, never switches branches.
#
# Usage: bash scripts/backup-personal.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKTREE="$REPO_ROOT/.personal-worktree"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"

# Ensure personal-main branch exists
if ! git -C "$REPO_ROOT" show-ref --quiet refs/heads/personal-main; then
  echo "Creating personal-main branch from main..."
  git -C "$REPO_ROOT" branch personal-main main
fi

# Ensure worktree exists on personal-main
if [ ! -d "$WORKTREE" ]; then
  echo "Setting up personal-main worktree..."
  git -C "$REPO_ROOT" worktree add "$WORKTREE" personal-main
fi

cd "$WORKTREE"

# Bring in any new framework commits from main
git merge main --no-edit -m "merge: framework from main — $TIMESTAMP" 2>/dev/null || true

# Copy personal data files from main working tree into worktree
PERSONAL_PATHS=("checkpoints" "data" "resumes" "config/user.json")
for path in "${PERSONAL_PATHS[@]}"; do
  src="$REPO_ROOT/$path"
  dst_dir="$(dirname "$WORKTREE/$path")"
  if [ -e "$src" ]; then
    mkdir -p "$dst_dir"
    cp -r "$src" "$dst_dir/"
  fi
done

# Stage all changes; force-add personal files that are gitignored in main
git add -A
git add -f checkpoints data resumes config/user.json 2>/dev/null || true

if git diff --cached --quiet; then
  echo "Nothing changed — career-os-sp:main already up to date."
else
  git commit -m "sync: personal data — $TIMESTAMP"
  echo "Committed personal data snapshot."
fi

# Push personal-main as main to private repo
git push git@github-career-os:shubhamcodess/career-os-sp.git personal-main:main
echo "✓ career-os-sp:main updated (framework + personal data)"

cd "$REPO_ROOT"
