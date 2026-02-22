---
name: security-review
description: Security-focused review of recent code changes. Checks for OWASP Top 10 vulnerabilities, secrets, injection risks, and authentication/authorisation issues. Use before merging any code that handles user input, authentication, or external data.
context: fork
agent: security-reviewer
allowed-tools: Read, Grep, Glob, Bash(git *)
disable-model-invocation: true
argument-hint: "[commit range or file paths, or leave blank for HEAD~1]"
---

# Security Review

Conduct a security-focused code review. You have no context from the conversation that produced this code — review it with fresh eyes and appropriate scepticism.

## Step 1 — Establish scope

- If $ARGUMENTS specifies a commit range or file paths, review those
- Otherwise: `git diff HEAD~1` for the diff, `git diff HEAD~1 --stat` for the file list
- Read the full current content of each changed file, not just the diff

## Step 2 — Identify the attack surface

Before running through the checklist, identify:
- Does this code handle user-supplied input? (HTTP request bodies, query params, file uploads, form data)
- Does this code authenticate or authorise users?
- Does this code query a database, run system commands, or interact with external services?
- Does this code handle secrets, tokens, or credentials?
- Does this code produce output that is rendered in a browser or terminal?

Document the attack surface — this shapes the severity of any findings.

## Step 3 — OWASP Top 10 checklist (2021)

For each item, note whether it is relevant to this code and whether it passes or fails.

**A01 — Broken Access Control**
- [ ] Every operation that modifies data or accesses sensitive resources checks authorisation
- [ ] Authorisation is enforced server-side, not only in the UI
- [ ] No path traversal vulnerabilities in file operations
- [ ] No insecure direct object references (user-controlled IDs accessing other users' data)

**A02 — Cryptographic Failures**
- [ ] No sensitive data (passwords, tokens, PII) stored or transmitted in plaintext
- [ ] Passwords are hashed with a strong adaptive algorithm (bcrypt, Argon2, scrypt)
- [ ] No use of deprecated cryptographic algorithms (MD5, SHA-1 for security purposes, DES)
- [ ] TLS enforced for any external communication

**A03 — Injection**
- [ ] All database queries use parameterised queries or a safe ORM — no string concatenation
- [ ] All system command execution uses safe APIs — no shell injection via string interpolation
- [ ] LDAP, XML, and other query languages are parameterised or sanitised
- [ ] Log injection is prevented (user input is not written to logs without sanitisation)

**A04 — Insecure Design**
- [ ] Security controls are designed into the architecture, not bolted on
- [ ] Sensitive operations have rate limiting or abuse prevention
- [ ] Trust boundaries are clearly defined and enforced

**A05 — Security Misconfiguration**
- [ ] No debug endpoints or verbose error messages exposed in production code paths
- [ ] No default credentials or empty passwords
- [ ] No unnecessary features, components, or permissions enabled

**A06 — Vulnerable and Outdated Components**
- [ ] No obviously outdated dependency versions with known CVEs
- [ ] No deprecated security APIs

**A07 — Identification and Authentication Failures**
- [ ] Session tokens are sufficiently random and invalidated on logout
- [ ] No hardcoded credentials or API keys
- [ ] Brute force protection exists for authentication endpoints

**A08 — Software and Data Integrity Failures**
- [ ] Deserialisation of untrusted data is handled safely
- [ ] Integrity of external resources (downloads, plugins) is verified

**A09 — Security Logging and Monitoring Failures**
- [ ] Security-relevant events are logged (login, authorisation failures, data access)
- [ ] Logs do not contain sensitive data (passwords, tokens, PII)
- [ ] Log entries include enough context for incident response

**A10 — Server-Side Request Forgery (SSRF)**
- [ ] URLs or hostnames supplied by users are validated against an allowlist before requests are made
- [ ] Internal network addresses are blocked from user-controlled URL parameters

## Step 4 — Secrets scan

Search the diff and all changed files for:
- Patterns matching API keys, tokens, passwords (use Grep for common patterns: `api_key`, `password`, `secret`, `token`, `Bearer `, `private_key`)
- Hardcoded IP addresses or internal hostnames
- Base64-encoded strings that may contain credentials

## Step 5 — Output

```
## Security Review

**Scope**: {commit range or files reviewed}
**Attack surface**: {brief description of what this code touches}

### Summary
{One paragraph. State clearly: no security issues found / issues found that must be fixed.}

### Critical Vulnerabilities (must fix immediately)
1. **{OWASP category}** — `{file}:{line}` — {description of the vulnerability and its impact}
   Remediation: {specific fix}

### Warnings (should fix before production)
1. **{OWASP category}** — `{file}:{line}` — {description}

### Informational
1. {Lower-severity observation}

### Secrets scan
{Findings, or "No hardcoded secrets found"}

### OWASP Top 10 checklist
| Category | Relevant? | Status |
|---|---|---|
| A01 Broken Access Control | Yes/No | Pass/Fail/N/A |
| A02 Cryptographic Failures | Yes/No | Pass/Fail/N/A |
| A03 Injection | Yes/No | Pass/Fail/N/A |
| A04 Insecure Design | Yes/No | Pass/Fail/N/A |
| A05 Security Misconfiguration | Yes/No | Pass/Fail/N/A |
| A06 Vulnerable Components | Yes/No | Pass/Fail/N/A |
| A07 Auth Failures | Yes/No | Pass/Fail/N/A |
| A08 Data Integrity Failures | Yes/No | Pass/Fail/N/A |
| A09 Logging Failures | Yes/No | Pass/Fail/N/A |
| A10 SSRF | Yes/No | Pass/Fail/N/A |
```
