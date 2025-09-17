from __future__ import annotations

from typing import Iterable

from starlette.types import ASGIApp, Receive, Scope, Send

try:
    from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
except Exception:  # pragma: no cover - only during type/import edge cases
    AuthenticatedUser = object  # type: ignore[misc,assignment]


def _parse_list_env(value: str | None) -> set[str]:
    if not value:
        return set()
    items: list[str] = [x.strip() for x in value.replace("\n", ",").split(",") if x.strip()]
    return {x.lower() for x in items}


class EmailWhitelistMiddleware:
    """ASGI middleware to enforce an email/domain whitelist on MCP HTTP requests.

    Expects an authentication middleware earlier in the chain that sets
    `scope["user"]` to an AuthenticatedUser with an `access_token.claims` mapping
    containing an "email" key (as provided by FastMCP's Google OAuth provider).

    Only enforces for the MCP endpoint path (default "/mcp"). Other routes like
    OAuth endpoints and health checks are left untouched.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        allowed_emails: Iterable[str] | None = None,
        allowed_domains: Iterable[str] | None = None,
        mcp_path: str = "/mcp",
    ) -> None:
        self.app = app
        self.allowed_emails = {e.lower() for e in (allowed_emails or [])}
        self.allowed_domains = {d.lower().lstrip("@") for d in (allowed_domains or [])}
        self.mcp_path = mcp_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if not path.startswith(self.mcp_path):
            await self.app(scope, receive, send)
            return

        # If no restrictions configured, allow
        if not self.allowed_emails and not self.allowed_domains:
            await self.app(scope, receive, send)
            return

        user = scope.get("user")

        # If user is not authenticated, let upstream auth middleware handle 401/403
        if not isinstance(user, AuthenticatedUser):
            await self.app(scope, receive, send)
            return

        claims = getattr(user, "access_token", None)
        email: str | None = None
        if claims and getattr(claims, "claims", None):
            claim_map = claims.claims  # type: ignore[attr-defined]
            email = claim_map.get("email") or (claim_map.get("google_user_data") or {}).get("email")

        if not email:
            # Deny if we cannot determine email and a whitelist is set
            await self._deny(send, 403, "forbidden", "Email not available for authorization")
            return

        email_l = email.lower()
        domain = email_l.split("@")[-1] if "@" in email_l else ""

        if (self.allowed_emails and email_l in self.allowed_emails) or (
            self.allowed_domains and domain in self.allowed_domains
        ):
            await self.app(scope, receive, send)
            return

        await self._deny(send, 403, "forbidden", "Email not whitelisted")

    @staticmethod
    async def _deny(send: Send, status_code: int, error: str, description: str) -> None:
        body = (f'{{"error":"{error}","error_description":"{description}"}}').encode()
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
