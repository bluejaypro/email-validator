import smtplib

import dns.resolver

from app.config import SMTP_FROM_ADDRESS, SMTP_TIMEOUT, DNS_TIMEOUT


def check_smtp(email: str) -> dict:
    """Verify the mailbox exists via SMTP conversation."""
    domain = email.rsplit("@", 1)[1].lower()

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT
        records = resolver.resolve(domain, "MX")
        mx_host = str(records[0].exchange).rstrip(".")
    except Exception:
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": False,
            "message": "Could not resolve mail server",
        }

    try:
        server = smtplib.SMTP(timeout=SMTP_TIMEOUT)
        server.connect(mx_host)
        server.helo(server.local_hostname)
        server.mail(SMTP_FROM_ADDRESS)
        code, _ = server.rcpt(email)
        server.quit()

        if code == 250:
            return {
                "name": "smtp",
                "label": "SMTP Verification",
                "passed": True,
                "message": "Mailbox verified",
            }
        elif code == 550:
            return {
                "name": "smtp",
                "label": "SMTP Verification",
                "passed": False,
                "message": "Mailbox does not exist",
            }
        else:
            return {
                "name": "smtp",
                "label": "SMTP Verification",
                "passed": None,
                "message": f"Inconclusive (server returned {code})",
            }

    except smtplib.SMTPConnectError:
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Could not connect to mail server",
        }
    except smtplib.SMTPServerDisconnected:
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Mail server disconnected",
        }
    except TimeoutError:
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Connection timed out",
        }
    except Exception:
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "SMTP check unavailable",
        }
