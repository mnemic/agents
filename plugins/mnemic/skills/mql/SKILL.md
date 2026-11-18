---
name: mql
description: Author, validate, and explain MQL (Mnemic Query Language) queries, schema changes, and migrations against a Mnemic database.
---

# MQL authoring

MQL is Mnemic's query and command language. Use this skill for MQL statements, schema evolution, migrations, and explanations of query behavior. The bundled [MQL reference](references/MqlReference/README.md) describes the language, and its index lists every topic by task; read only the topics the task needs. The rest of the bundled [manual](references/README.md) covers installing, configuring and operating a server, and the clients.

## Workflow

1. Discover the schema before choosing fields or relations. Use supplied DDL, `DESCRIBE COLLECTION [Ns].[Collection]`, or the relevant [system collections](references/MqlReference/system-collections.md).
2. Read the topic's syntax and usage pitfalls. MQL queries start with `FROM`, collection identities use `[Namespace].[Collection]`, and clause ordering is strict. Brackets always work for a user-defined name, and nearly every position requires them: fields, databases, enums, reusable types, relation aliases, and named windows. The `ON DATABASE` scope of the user and role administration statements also accepts a plain identifier ([authentication](references/MqlReference/auth-admin.md)). Use `[Namespace].[TypeName]` or `[TypeName]` at the top level. See [enums](references/MqlReference/enums.md) and [composite types](references/MqlReference/composite-types.md) for declarations and references. Do not substitute SQL syntax based on resemblance.
3. Separate script statements with semicolons using the lexical rules in [syntax](references/MqlReference/syntax.md). A line break does not end a statement. Use [parameters](references/MqlReference/parameters.md) for values. Keep schema identities explicit and check their statement-specific grammar.
4. For schema changes, follow [migration boundaries](references/MqlReference/migrations.md). Online index DDL is standalone; check [indexes](references/MqlReference/indexes.md). A failed explicit transaction requires rollback and retry of the transaction.
5. Validate the complete statement against the known schema. On a connected server, `VALIDATE @text` reports what in the text does not parse as that server reads it, without running anything ([editor assistance](references/MqlReference/editor-assistance.md)); `EXPLAIN` plans a query without executing it, while `EXPLAIN ANALYZE` executes. Report whether the statement was executed, validated by a server, or only reviewed.
6. Explain relevant NULL, temporal, cardinality, and mutation semantics using the corresponding reference. Do not infer exact results without data.

## Common pitfalls

Each rule is owned by the linked section; read it before relying on the rule.

- `BEGIN MIGRATION` takes the database's current schema level: [migrations](references/MqlReference/migrations.md).
- Separate script statements with `;`; a request carries one statement, and a script's last statement may end at EOF: [multi-statement execution](references/MqlReference/syntax.md#multi-statement-execution).
- Collection options come before `EXTENDS`: [CREATE COLLECTION](references/MqlReference/ddl.md#create-collection).
- One `INSERT` lists up to 1,000 documents, in one transaction, with every clause applying to each; a refusal names its row: [multi-row INSERT](references/MqlReference/dml.md#multi-row-insert).
- An alias that repeats an input field's name needs a qualified input or `SELECT * REPLACE`: [alias rules](references/MqlReference/queries.md#alias-repeating-an-input-field).
- `WINDOW` follows `SELECT`: [clause ordering](references/MqlReference/queries.md#syntax-clause-ordering--strict).
- Enum fields take underlying values, never labels: [document literals](references/MqlReference/document-literals.md).
- Temporal text is ISO 8601 only: [temporal text](references/MqlReference/document-literals.md#temporal-text).
- `SELECT SUBTYPE` yields the `_type` column: [querying by subtype](references/MqlReference/polymorphism.md#querying-by-subtype).
- A plain `[Meta].[X]` item returns the whole `Meta` object: [Meta fields](references/MqlReference/system-collections.md#meta-fields).
- A `JOIN` takes only its query's `AS OF`; under `IN BETWEEN` or `LAST PER` the joined collection reads its current versions: [temporal](references/MqlReference/temporal.md#in-between-temporal-range).
- Any failed or refused statement rolls back the open migration, a parse error, online index DDL and `BEGIN TRANSACTION` or `COMMIT` included: [failed statements](references/MqlReference/migrations.md#a-failed-statement-ends-the-migration).
- There is no `IF EXISTS` / `IF NOT EXISTS`: [syntax pitfalls](references/MqlReference/syntax.md#pitfall-there-is-no-if-exists-or-if-not-exists).

## Find the relevant topic

The [reference index](references/MqlReference/README.md) lists every topic by task. Read [syntax](references/MqlReference/syntax.md) for the lexical rules, [errors](references/MqlReference/errors.md) to diagnose a failure, and [examples](references/MqlReference/examples.md) for complete queries to adapt.

## When the answer is uncertain

Treat the reference as the language contract. It describes the Mnemic release this skill was published with, and `FROM [Mnemic].[Version]` names the version of the server you are connected to. When the server disagrees with the reference, such as a `VALIDATE` failure on syntax the reference documents, report the discrepancy and the server's version rather than inventing syntax or promising unsupported behavior.
