# Fraime

Full product context in [idea.md](idea.md). Summary:

Open source AI video generation platform that automatically detects available
hardware capacity and selects the best possible model to generate video,
avoiding closed platforms' paywalls and the friction of implementing open
source models on your own.

## Products / Components

The repository is organized as one directory per component, at the root:

- `api/` — Video generation engine, model detection engine,
  authentication/authorization, sensitive data security, cloud integration.
- `sdk/` — Programmatic access to the API to integrate video generation into
  workflows (versioned in parallel with the API, auth, multi-language support).
- `mcp/` — MCP server for agentic access to the API from AI workflows
  (generalized context, endpoint customization).

Each component is self-contained: its dependencies, configuration, tests, and
documentation live inside its own folder, not at the root or mixed with
another component.

## Component isolation rule

**A change requested for one component must not touch files in another
component.**

- If the task is about `api/`, nothing inside `sdk/` or `mcp/` is modified,
  and vice versa.
- If a change in one component requires adjusting another (e.g. the SDK needs
  to reflect a contract change in the API), that is treated as a separate
  task: it is flagged explicitly to the user instead of being done implicitly
  as part of the same change.
- Files that are genuinely shared across the whole repo (this `CLAUDE.md`,
  `idea.md`, root-level CI/repo configuration) are the only exception, and are
  only touched when the requested change is explicitly repo-level, not
  component-level.
- When it's ambiguous which component a change belongs to, ask before
  touching code in more than one folder.

## Git operations rule

**Never run git operations that modify the repository or remote state** —
this includes `git add`, `git commit`, and, even more so, `git push`. Also do
not run other destructive or history-altering operations (`git reset`,
`git rebase`, `git merge`, creating/deleting branches, etc.).

- Read-only commands (`git status`, `git diff`, `git log`, `git show`, etc.)
  can be used freely to understand repo state.
- The user decides when to stage, commit, or push their changes.
