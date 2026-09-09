# Security policy

Agent Plugins Author is intentionally a skills-only package. It should not
contain secrets, private keys, personal access tokens, credential-bearing MCP
headers, or machine-local connection identifiers.

Do not report a suspected vulnerability in a public issue if it includes
sensitive data. Use a private GitHub security advisory for this repository when
available. For non-sensitive defects, open a GitHub issue with a minimal
reproduction and no credentials.

Upstream refresh reads only allowlisted public sources. It must fail closed when
the source is unavailable or conflicting and must not mutate the accepted
baseline during refresh.
