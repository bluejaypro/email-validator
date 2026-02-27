import asyncio

import dns.resolver

from app.config import DNS_TIMEOUT


def check_mx(email: str) -> dict:
    """Verify MX records exist for the email domain."""
    domain = email.rsplit("@", 1)[1].lower()

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT
        records = resolver.resolve(domain, "MX")

        if records:
            mx_host = str(records[0].exchange).rstrip(".")
            return {
                "name": "mx",
                "label": "MX Record",
                "passed": True,
                "message": f"Mail server found ({mx_host})",
            }

    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoNameservers:
        pass
    except dns.resolver.LifetimeTimeout:
        return {
            "name": "mx",
            "label": "MX Record",
            "passed": False,
            "message": "DNS lookup timed out",
        }
    except Exception:
        pass

    return {
        "name": "mx",
        "label": "MX Record",
        "passed": False,
        "message": "No mail server found for this domain",
    }


async def check_mx_async(email: str) -> dict:
    """Async version - runs blocking DNS lookup in a thread."""
    return await asyncio.to_thread(check_mx, email)
