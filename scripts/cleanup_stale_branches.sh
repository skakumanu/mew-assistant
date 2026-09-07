#!/usr/bin/env bash
#
# Delete remote branches that are no longer doing anything: ones with a
# merged or closed pull request and nothing open pointing at them. Defaults
# to a dry run - nothing is deleted until you pass --execute.
#
# This repo currently has ~90 remote branches (a year of feature/, hotfix/,
# and sync-develop.yml's auto-generated ci/sync-develop-* branches), most of
# them long since merged and just sitting there. This script clears those
# out without touching anything Dependabot or an open PR still needs.
#
# Never touches: master, develop, dependabot/* (Dependabot owns those - it
# recreates them on its own schedule and several may have open PRs right
# now), or any branch with an open PR of its own.
#
# A branch with NO pull request at all (opened straight in git, never
# PR'd) is never auto-deleted - it's listed separately for you to check by
# hand, since it might be someone's in-progress work.
#
# Usage:
#   scripts/cleanup_stale_branches.sh            # dry run - lists what would be deleted
#   scripts/cleanup_stale_branches.sh --execute  # actually deletes them, after a y/n prompt
#
# Requires: git, and the GitHub CLI (`gh`), authenticated (`gh auth login`).
# Override the repo with MEW_REPO=owner/name if you're running this
# somewhere other than a clone of skakumanu/mew-assistant.

set -euo pipefail

REPO="${MEW_REPO:-skakumanu/mew-assistant}"
PROTECTED_REGEX='^(master|develop)$'
NEVER_TOUCH_REGEX='^dependabot/'
EXECUTE=false

for arg in "$@"; do
  case "$arg" in
    --execute) EXECUTE=true ;;
    -h|--help)
      sed -n '2,29p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg (use --execute or --help)" >&2
      exit 1
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "This script needs the GitHub CLI ('gh'). Install it and run 'gh auth login' first." >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "'gh' isn't authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

echo "Fetching remote branches for $REPO..."
git fetch origin --prune --quiet

mapfile -t all_branches < <(git branch -r --format='%(refname:short)' | sed 's#^origin/##' | grep -v '^HEAD$')

echo "Fetching open PR head branches..."
mapfile -t open_pr_branches < <(gh pr list --repo "$REPO" --state open --json headRefName --jq '.[].headRefName')

is_open_pr_branch() {
  local b="$1"
  local o
  for o in ${open_pr_branches[@]+"${open_pr_branches[@]}"}; do
    [[ "$b" == "$o" ]] && return 0
  done
  return 1
}

to_delete=()
skipped_no_pr=()
total=${#all_branches[@]}
i=0

for branch in "${all_branches[@]}"; do
  i=$((i + 1))
  [[ "$branch" =~ $PROTECTED_REGEX ]] && continue
  [[ "$branch" =~ $NEVER_TOUCH_REGEX ]] && continue
  is_open_pr_branch "$branch" && continue

  printf '\rChecking PR history: %d/%d' "$i" "$total" >&2

  # Ground truth on whether this branch's work landed: its own PR history,
  # not local git ancestry - a squash-merged branch is not an ancestor of
  # develop even though every line it added is already there.
  state=$(gh pr list --repo "$REPO" --state all --head "$branch" \
    --json state,mergedAt --jq '.[0] | if .mergedAt then "merged" elif .state == "CLOSED" then "closed" else "open" end' \
    2>/dev/null || true)

  case "$state" in
    merged | closed) to_delete+=("$branch") ;;
    "") skipped_no_pr+=("$branch") ;;
    # "open" here would mean a race with a PR that opened mid-run; leave it.
  esac
done
printf '\n' >&2

echo
echo "=== Safe to delete - merged or closed PR, nothing open (${#to_delete[@]}) ==="
printf '  %s\n' "${to_delete[@]:-}"

echo
echo "=== No pull request found - review by hand, not auto-deleted (${#skipped_no_pr[@]}) ==="
printf '  %s\n' "${skipped_no_pr[@]:-}"

if [[ "$EXECUTE" != true ]]; then
  echo
  echo "Dry run only - nothing was deleted. Re-run with --execute to delete the ${#to_delete[@]} branches above."
  exit 0
fi

if [[ ${#to_delete[@]} -eq 0 ]]; then
  echo
  echo "Nothing to delete."
  exit 0
fi

echo
read -rp "About to delete ${#to_delete[@]} remote branches from origin. Type 'yes' to continue: " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "Aborted - nothing was deleted."
  exit 1
fi

failed=()
for branch in "${to_delete[@]}"; do
  echo "Deleting origin/$branch..."
  git push origin --delete "$branch" || failed+=("$branch")
done

echo
echo "Deleted $(( ${#to_delete[@]} - ${#failed[@]} )) of ${#to_delete[@]} branches."
if [[ ${#failed[@]} -gt 0 ]]; then
  echo "Failed to delete:"
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
