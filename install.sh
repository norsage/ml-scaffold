#!/usr/bin/env bash
# Install the ml-scaffold skill into ~/.agents/skills/, linked from
# ~/.claude/skills/. Only globally: the skill sets projects up and is not
# needed in them afterwards (a project keeps its revision in skills.lock).
#
# Usage:
#   bash install.sh                  # copy (default)
#   bash install.sh --symlink        # symlink instead of copy (skill devs)
#
# Re-running is idempotent: existing installs are replaced after a prompt.
#
# .agents/skills/ is read by Codex, OpenCode, Cursor, Copilot and Gemini CLI;
# Claude Code reads only .claude/skills/, so it gets a relative symlink to the
# skill. Tools that read both directories see the skill twice.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="ml-scaffold"

if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
    echo "error: $SCRIPT_DIR doesn't look like the skill source (no SKILL.md)" >&2
    exit 1
fi

MODE="copy"

while [ $# -gt 0 ]; do
    case "$1" in
        --symlink) MODE="symlink"; shift ;;
        --copy)    MODE="copy"; shift ;;
        --project)
            echo "ml-scaffold is installed only globally: a project keeps its revision in skills.lock" >&2
            exit 2
            ;;
        -h|--help)
            sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            exit 2
            ;;
    esac
done

BASE="$HOME"
TARGET="$BASE/.agents/skills/$SKILL_NAME"
LINK="$BASE/.claude/skills/$SKILL_NAME"

mkdir -p "$(dirname "$TARGET")" "$(dirname "$LINK")"

existing=""
for p in "$TARGET" "$LINK"; do
    if [ -e "$p" ] || [ -L "$p" ]; then existing="$existing $p"; fi
done
if [ -n "$existing" ]; then
    echo "existing install will be replaced:$existing"
    if [ -t 0 ]; then
        printf "continue? [y/N] "
        read -r ans
        case "$ans" in
            y|Y|yes|YES) ;;
            *) echo "aborted."; exit 1 ;;
        esac
    fi
    rm -rf "$TARGET" "$LINK"
fi

if [ "$MODE" = "symlink" ]; then
    ln -s "$SCRIPT_DIR" "$TARGET"
    echo "symlinked $SCRIPT_DIR -> $TARGET"
else
    # Copy everything the agent reads at runtime. docs/ (this skill's own
    # board), tests/ and the development environment (pyproject.toml, uv.lock)
    # stay in the checkout; --symlink installs it whole.
    if command -v rsync >/dev/null 2>&1; then
        rsync -a \
            --exclude='/.git' --exclude='/.gitignore' --exclude='.DS_Store' \
            --exclude='__pycache__' --exclude='*.pyc' \
            --exclude='/docs' --exclude='/tests' --exclude='.pytest_cache' \
            --exclude='/pyproject.toml' --exclude='/uv.lock' --exclude='/.venv' --exclude='.ruff_cache' \
            "$SCRIPT_DIR/" "$TARGET/"
    else
        mkdir -p "$TARGET"
        (cd "$SCRIPT_DIR" && \
         find . -type f \
            -not -path './.git/*' -not -path './.gitignore' -not -name '.DS_Store' \
            -not -path '*/__pycache__/*' -not -name '*.pyc' \
            -not -path './docs/*' -not -path './tests/*' -not -path '*/.pytest_cache/*' \
            -not -path './pyproject.toml' -not -path './uv.lock' -not -path './.venv/*' -not -path '*/.ruff_cache/*' \
            -print0 | \
         while IFS= read -r -d '' f; do
            mkdir -p "$TARGET/$(dirname "$f")"
            cp "$f" "$TARGET/$f"
         done)
    fi
    # The revision the copy came from: install_components.py records it in a
    # project's skills.lock.
    if rev=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null); then
        [ -z "$(git -C "$SCRIPT_DIR" status --porcelain 2>/dev/null)" ] || rev="$rev-dirty"
        echo "$rev" > "$TARGET/VERSION"
    fi
    # Where the copy came from, for the same record; none without a remote.
    if url=$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null); then
        echo "$url" > "$TARGET/SOURCE"
    fi
    echo "installed $SKILL_NAME to $TARGET"
fi

ln -s "../../.agents/skills/$SKILL_NAME" "$LINK"
echo "linked $LINK -> ../../.agents/skills/$SKILL_NAME (Claude Code)"
