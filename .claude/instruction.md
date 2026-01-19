## Execution Policy

You are an AI assistant that always provides full, uninterrupted answers.
Never stop mid-output unless you reach a hard token limit.
If containers should be stopped and rebuilt, then run
  docker compose stop
  docker compose up -d

When debugging, make sure to check if container should be deleted and re-created so the fix can take effect
Task acceptance criteria is that you can run end-to-end test to validate the fix.

- Do not ask for confirmation before proceeding.
- Do not pause after intermediate steps.
- Assume approval for file edits, refactors, and command execution.
- Continue until the task is fully complete.
- Only stop if an irreversible or destructive action would cause data loss.
