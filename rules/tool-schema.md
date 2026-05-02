# Tool Schema Rules

Rules for designing tool definitions exposed to LLM agents (function calling, MCP tools, Anthropic tools, etc.). Aligned with the [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) skill.

---

## Naming

1. **Verb-noun, snake_case, lowercase.**
   - ✅ `read_file`, `search_code`, `create_branch`
   - ❌ `ReadFile`, `rd_f`, `fileReader`

2. **Match user vocabulary, not implementation details.**
   - ✅ `search_code`
   - ❌ `ripgrep_invoke`, `elastic_query`

3. **No abbreviations.** Spell it out unless universally understood.
   - ✅ `delete_repository`
   - ❌ `del_repo`

4. **No two tools with overlapping purpose.** Pick one or split clearly.
   - ❌ Having both `find_file` and `search_file`
   - ✅ One tool with clear scope, or two with non-overlapping descriptions

5. **Namespace tools when servers compose.** MCP servers should prefix their tools (`gh_create_pr`, `slack_send_message`).

---

## Description

6. **First sentence is the trigger query.** This is what the model matches against intent.
   - ✅ `"Reads a file from the local filesystem and returns its contents."`
   - ❌ `"This is a useful tool for various file operations."`

7. **State when to use AND when not to use.**
   ```
   Use this when:
     - The user references a specific file path
     - You need to inspect code or config
   Do not use for:
     - Listing files (use list_dir)
     - Searching across files (use search_code)
   ```

8. **Document the return shape.** Truncated? Paginated? Always-available? Errors?

9. **Cross-reference sibling tools.** "For listing directory contents, see `list_dir` instead."

10. **Embed trigger keywords early.** First 100 chars matter most for selection. Front-load words the user might say.

---

## Parameters

11. **Every parameter has a `description`.** No exceptions, even for "obvious" params like `path`.

12. **Use precise types.**
    - `"type": "integer"` for counts (not `"number"`)
    - `"type": "string"` with `format` when applicable
    - `"type": "boolean"` for flags

13. **Use `enum` for fixed choices.**
    ```json
    "status": {
      "enum": ["open", "closed", "merged"],
      "description": "PR status to filter by."
    }
    ```

14. **Mark required vs optional explicitly** in the schema's `required` array.

15. **Document defaults in description.**
    - ✅ `"limit": {"type": "integer", "description": "Max items. Default: 100."}`
    - ❌ Implicit defaults the model has to guess

16. **Use `minimum`, `maximum`, `pattern` for constraints.** Helps the model produce valid args without trial-and-error.

17. **Provide examples for complex parameters.** Especially when format is non-obvious (regex, datetimes, structured strings).

---

## Return Shape

18. **Return structured information, not free-text wall.**
    - ✅ `{"matches": [{"file": "...", "line": 5, "snippet": "..."}]}`
    - ❌ `"Found 3 matches in 2 files: foo.ts line 5 has 'pattern', bar.ts..."`

19. **Bound the size.** Truncate at a known limit; mark the truncation explicitly.

20. **Include metadata for the model to reason about.** Total count, has-more flag, suggestions.

21. **Distinguish "no result" from "tool failed".**
    - Empty result: `{"matches": []}`
    - Tool failure: `{"error": "PERMISSION_DENIED", ...}`

---

## Errors

22. **Errors are part of the contract.** Return structured errors the model can react to.
    ```json
    {"error": "FILE_NOT_FOUND", "path": "/foo/bar", "suggestion": "Try list_dir to find the correct path"}
    ```

23. **Suggest a recovery path** when possible. The model needs to know what to try next.

24. **Don't leak implementation details.** Strip stack traces, internal IDs, transient state.

25. **Unrecoverable errors should be marked.**
    - `{"error": "PERMISSION_DENIED", "fatal": true}` — don't retry
    - `{"error": "RATE_LIMITED", "retry_after_s": 30}` — retry after wait

---

## Side Effects & Safety

26. **Mark destructive operations explicitly in the description.**
    - ✅ `"Permanently deletes the branch. This is irreversible."`
    - ❌ Hidden in name only (`delete_branch`)

27. **Read-only tools don't need confirmation language.** Encourages safe exploration.

28. **Mutating tools should suggest confirmation in description** when blast radius is high.

29. **Match credentials to capability.** A read-only tool should use a read-only credential. Don't share root.

30. **Provide dry-run / preview modes** for destructive operations where useful.

---

## Granularity

31. **Aim for 5-15 tools per agent.** Below 5 = limited; above 15 = poor selection without lazy loading.

32. **Each tool does one thing.** `read_file` good. `read_or_write_file` bad.

33. **Don't expose every API endpoint.** Curate the 10-15 the agent actually needs.

34. **Use resources for read-only addressable data; tools for actions.** (MCP especially.)

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `"args": {"type": "string"}` catch-all | Define each arg as its own typed property |
| `run_command` with no allowlist | Specific tools per command, or strict allowlist |
| Tool description: `"Reads a file."` | Add when-to-use, when-not-to-use, return shape |
| Multiple tools with same prefix doing different things (`get_data`, `fetch_data`, `read_data`) | One tool, clear name |
| Throwing exceptions for expected failures | Return structured error |
| Returning raw 50K-token blobs | Truncate; mark truncation; offer pagination |
| Optional params without documented defaults | State the default in description |
| Boolean dummy params for variant logic | Split into distinct tools or use enum |
