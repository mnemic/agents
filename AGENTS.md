# Mnemic agent plugins — repository rules

This repository publishes the Claude Code marketplace `mnemic` and its plugin `mnemic`. The plugin's MQL skill carries the Mnemic manual, the MQL reference among it, which lives in [mnemic/docs](https://github.com/mnemic/docs) and is pinned here as a submodule. Why the three repositories are split this way, and how their versions relate, is recorded in the Mnemic engine repository's decision on the public docs and agent plugins.

## Layout

| Path | What it is |
|---|---|
| `.claude-plugin/marketplace.json` | The marketplace and the plugins it lists. |
| `plugins/mnemic/.claude-plugin/plugin.json` | The plugin's manifest. Its `version` is the one version of the plugin and of the portable skill package. |
| `plugins/mnemic/skills/mql/SKILL.md` | The MQL authoring workflow and pitfalls. It finds topics through the MQL reference's own index. |
| `plugins/mnemic/skills/mql/references/` | Submodule: [mnemic/docs](https://github.com/mnemic/docs), the whole manual; the MQL reference is its `MqlReference/`. Never edit it here. |
| `Scripts/package-mql-skill.sh` | Builds the portable skill ZIP from a clean checkout and verifies it against its sources. |

## Rules

- **The manual is edited only in mnemic/docs**, together with the engine change it describes, where the engine's tests check it; this repository only moves its pin. The pin is a commit on mnemic/docs `main`; for a Mnemic release it is the commit that release pins, tagged with the release's version.
- **Every change under `plugins/` bumps `version` in `plugin.json`.** Claude Code installs a plugin by its version, so a change pushed under an old version never reaches an installed plugin. The major version is the Mnemic major version the plugin serves; minor and patch are the plugin's own. The pull-request qualification refuses a changed plugin with an unchanged version.
- **SKILL.md holds the workflow and the pitfalls, never language rules.** Each pitfall links to the reference section that owns it, and topics are found through `references/MqlReference/README.md`, so a new topic needs no change here.
- **Commits.** Work on `feature/<slug>` or `fix/<slug>` branches and never commit to `main`; landing work there is the maintainer's job. A commit message is one headline line, without AI-attribution trailers.
- **Prose is never hard-wrapped.** Each paragraph, list item and blockquote is one line.

## Checks

```shell
git submodule update --init
python -m unittest discover -s Scripts -p test_mql_skill_package.py
bash Scripts/package-mql-skill.sh --output-directory <directory>
claude plugin validate .
```
