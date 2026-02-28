import asyncio
import logging
import smtplib

import dns.resolver

from app.config import SMTP_FROM_ADDRESS, SMTP_TIMEOUT, DNS_TIMEOUT

logger = logging.getLogger("email_validator.smtp")


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
        logger.debug("SMTP: could not resolve MX for %s", domain)
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
            logger.info("SMTP inconclusive for %s: code %d", email, code)
            return {
                "name": "smtp",
                "label": "SMTP Verification",
                "passed": None,
                "message": f"Inconclusive (server returned {code})",
            }

    except smtplib.SMTPConnectError:
        logger.warning("SMTP connect failed for %s via %s", email, mx_host)
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Could not connect to mail server",
        }
    except smtplib.SMTPServerDisconnected:
        logger.warning("SMTP server disconnected for %s", email)
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Mail server disconnected",
        }
    except (TimeoutError, OSError):
        logger.warning("SMTP timeout for %s via %s", email, mx_host)
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "Connection timed out",
        }
    except smtplib.SMTPException:
        logger.warning("SMTP error for %s", email, exc_info=True)
        return {
            "name": "smtp",
            "label": "SMTP Verification",
            "passed": None,
            "message": "SMTP check unavailable",
        }


async def check_smtp_async(email: str) -> dict:
    """Async version - runs blocking SMTP conversation in a thread."""
    return await asyncio.to_thread(check_smtp, email)
