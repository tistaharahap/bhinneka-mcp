# Authentication (Google OAuth) for Bhinneka MCP

This server supports protecting the HTTP MCP endpoint () with Google OAuth and an optional email/domain allowlist.

- Stdio transport remains unauthenticated for local development.
- HTTP transport can be protected with Google OAuth.
- You can additionally restrict access to specific email addresses or domains.

## Overview

When HTTP transport is used, the server can be configured to require a Bearer token (Google OAuth access token). The token is verified against Google and user claims (including ) are extracted. If an email/domain allowlist is configured, only matching users are permitted to access .

A helper endpoint  returns the current authentication context (safe subset) to aid debugging.

## Environment Variables

Google OAuth (via FastMCP GoogleProvider):
-  (required)
-  (required)
-  (optional)
  - Public base URL of this server (e.g., ). If not provided, defaults to  based on the CLI flags.
-  (optional, default: )
-  (optional)
  - Space- or comma-separated list. If not set, the server requests:  to ensure the email claim is available for whitelisting.

Email/domain allowlist (optional):
- 
  - Comma- or newline-separated list of exact email addresses to allow.
  - Example: 
- 
  - Comma- or newline-separated list of domains to allow (without ).
  - Example: 

Notes:
- If no allowlist variables are set, all authenticated Google accounts are allowed.
- Allowlist is only enforced for the MCP endpoint path ; OAuth and metadata endpoints remain accessible.

## How It Works

- The server uses FastMCP’s built-in Google OAuth provider, which exposes the necessary OAuth endpoints and validates Google access tokens.
- A Starlette middleware () runs after authentication and checks the user’s email claim against the configured allowlist.
- Unauthorized users receive a 403 response for  requests.

## Usage

1) Start the server in HTTP mode:



2) Set environment variables for Google OAuth:



3) Optionally, set allowlists:



4) Access helper endpoint to confirm auth context:



If you prefer an infrastructure approach, you can front the server with a reverse proxy that handles Google OAuth (e.g., oauth2-proxy) and forwards the  header—leave app-level OAuth disabled in that case.

## Security Considerations

- Use HTTPS in production and set  to your public URL.
- Don’t log tokens or PII; the server avoids logging sensitive data.
- Ensure the requested scopes include  so email is available for whitelisting.
- The stdio transport is intended for local, trusted environments; do not expose stdio over the network.

## Troubleshooting

- 401 Unauthorized: Missing or invalid Bearer token; complete Google OAuth and pass the .
- 403 Forbidden: Email not in the allowlist; update  or use a permitted account.
-  shows : Token not recognized; verify header formatting and token freshness.

