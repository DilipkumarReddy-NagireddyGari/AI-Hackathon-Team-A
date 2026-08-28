# Security notes

## Reporting

Do not include credentials, prompts, document text, generated content, or translation content in issue reports or logs.

## Prototype credential incident

The credential previously embedded in the prototype notebook has been removed from the working tree. Removal does not invalidate the credential and does not erase copies from Git history, backups, chat, or shared archives.

The credential owner must:

1. revoke or rotate the exposed credential in the provider console;
2. verify that the old credential can no longer authenticate;
3. scan and, where required, rewrite repository history and shared artifacts; and
4. record non-secret evidence of revocation before T01 is accepted.

Never place the replacement value in source, notebooks, examples, logs, screenshots, or test fixtures. Use a local ignored `.env` file or process environment variables.
