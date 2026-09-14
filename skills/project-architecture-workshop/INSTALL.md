# Use the workshop skill

Copy the entire `project-architecture-workshop` folder, including references and assets, into the chosen skill directory. Do not copy only SKILL.md or replace an existing installation without checking it.

| Tool | Personal installation | Project installation | Invocation |
|---|---|---|---|
| Codex | `~/.agents/skills/project-architecture-workshop/` | `<repo>/.agents/skills/project-architecture-workshop/` | `$project-architecture-workshop` |
| Claude Code | `~/.claude/skills/project-architecture-workshop/` | `<repo>/.claude/skills/project-architecture-workshop/` | `/project-architecture-workshop` |

These locations follow the [Codex skill documentation](https://learn.chatgpt.com/docs/build-skills) and [Claude Code skill documentation](https://code.claude.com/docs/en/skills), checked 2026-09-14. Start a new session and confirm the skill is listed. Tool access and independent-agent availability depend on the host; installation does not grant repository credentials or publishing permission.

Example request: "Use the workshop skill on this repository. Inspect the existing structure, create missing planning sources, and work through the important questions with me."

The package is portable and has no Maestro runtime dependency. Its source format is derived from the Maestro Planning Guide, but no Maestro system design, branch policy, model selection, or milestone content is a default for another project. The guide bundled here is a versioned copy for this skill; changes to the original guide are not automatically imported.

This instruction skill directs the coding agent's work. It is not a background service or a deterministic enforcement engine. Code changes, registration execution, and deployment remain separate tasks.

