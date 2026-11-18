# Mnemic agent plugins

Plugins that teach AI coding agents to work with [Mnemic](https://mnemic.io) databases.

## The mnemic plugin

The `mql` skill writes, checks and explains MQL queries, schema changes and migrations. It carries the [Mnemic manual](https://github.com/mnemic/docs) of the release it was published with, the MQL reference among it, so an agent reads the language's rules instead of guessing them from SQL.

### Claude Code

```text
/plugin marketplace add mnemic/agents
/plugin install mnemic@mnemic
```

`/plugin marketplace update mnemic` fetches a newer version.

### Other agents

Codex and Cursor read skills from `~/.agents/skills/`, and Codex, Cursor and VS Code read a project's `.agents/skills/`. Clone this repository with the manual and copy the skill there:

```shell
git clone --recurse-submodules https://github.com/mnemic/agents.git
mkdir -p ~/.agents/skills
cp -r agents/plugins/mnemic/skills/mql ~/.agents/skills/
rm ~/.agents/skills/mql/references/.git
```

## Versions

The plugin's major version is the Mnemic major version it serves: 1.x is for Mnemic 1.x. Its manual describes the Mnemic release it was published with; on a connected server, the skill reads the server's version from `[Mnemic].[Version]` and has the server check a statement with `VALIDATE` before relying on it.
