"""Prompt templates for commit message generation."""

import textwrap
from typing import Final

PROMPT_HEADER: Final[str] = textwrap.dedent(
    """\
    Your task is to help the user to generate a commit message and commit the changes using git.

    ## Guidelines
    - DO NOT add any ads such as "Generated with [Claude Code](https://claude.ai/code)"
    - Only generate the message for staged files/changes
    - Don't add any files using `git add`. The user will decide what to add.
    - Follow the rules below for the commit message.

    ## Format
    ```
    <type>: <message title>

    <summary title in one line>
    <bullet points summarizing what was updated>
    ```

    ## Example Titles
    ```
    feat(auth): add JWT login flow
    fix(ui): handle null pointer in sidebar
    refactor(api): split user controller logic
    docs(readme): add usage section
    ```

    ## Example with Title, Summary and Body
    ```
    feat(auth): add JWT login flow

    Authentication System Enhancement
    - Implemented JWT token validation logic
    - Added documentation for the validation component
    ```

    ## Rules
    * title is lowercase, no period at the end.
    * Title should be a clear summary, max 50 characters.
    * Add a single-line summary title that captures the high-level purpose of the changes.
    * Use the body (optional) to explain *why*, not just *what*.
    * Bullet points should be concise and high-level.

    Avoid
    * Vague titles like: "update", "fix stuff"
    * Overly long or unfocused titles
    * Excessive detail in bullet points
    * Repeating the commit title in the summary

    ## Allowed Types

    | Type     | Description                           |
    | -------- | ------------------------------------- |
    | feat     | New feature                           |
    | fix      | Bug fix                               |
    | chore    | Maintenance (e.g., tooling, deps)     |
    | docs     | Documentation changes                 |
    | refactor | Code restructure (no behavior change) |
    | test     | Adding or refactoring tests           |
    | style    | Code formatting (no logic change)     |
    | perf     | Performance improvements              |

    ---
    Below is the **staged diff**. Generate a commit message following the rules above:
    """
)

