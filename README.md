# Mnemic agent plugins

Plugins that teach AI coding agents to work with [Mnemic](https://mnemic.io) databases.

## The mnemic plugin

The `mql` skill writes, checks and explains MQL queries, schema changes and migrations. It carries the [MQL reference](https://github.com/mnemic/mql) of the Mnemic release it was published with, so an agent reads the language's rules instead of guessing them from SQL.

### Claude Code

```text
/plugin marketplace add mnemic/agents
/plugin install mnemic@mnemic
```

`/plugin marketplace update mnemic` fetches a newer version.

### Other agents

Codex and Cursor read skills from `~/.agents/skills/`, and Codex, Cursor and VS Code read a project's `.agents/skills/`. Clone this repository with the reference and copy the skill there:

```shell
git clone --recurse-submodules https://github.com/mnemic/agents.git
mkdir -p ~/.agents/skills
cp -r agents/plugins/mnemic/skills/mql ~/.agents/skills/
rm ~/.agents/skills/mql/references/.git
```

## Versions

The plugin's major version is the Mnemic major version it serves: 1.x is for Mnemic 1.x. A minor release of Mnemic adds to MQL without changing what it already accepts, so the newest 1.x skill also serves an older 1.x server, and the skill has the server check a statement with `VALIDATE` before relying on it.
