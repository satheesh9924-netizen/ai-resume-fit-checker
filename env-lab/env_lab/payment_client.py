"""The Orders service's view of the Payment service (the 'consumer').

It maps every failure to a clear outcome instead of hanging or throwing:
that behaviour is what the resilience tests check.
"""
import json
import urllib.error
import urllib.request
import socket
from collections import namedtuple

Result = namedtuple("Result", "status payment_id")


class PaymentClient:
    def __init__(self, base_url, timeout=5.0):
        self.base_url = base_url
        self.timeout = timeout

    def charge(self, order_id, amount_minor, currency, idempotency_key):
        body = json.dumps({"orderId": order_id, "amountMinor": amount_minor, "currency": currency}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/payments", data=body, method="POST",
            headers={"Content-Type": "application/json", "Idempotency-Key": idempotency_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return Result(payload.get("status"), payload.get("paymentId"))
        except urllib.error.HTTPError as error:
            return Result("UNAVAILABLE" if error.code >= 500 else "REJECTED", None)
        except (socket.timeout, TimeoutError):
            return Result("TIMEOUT", None)
        except urllib.error.URLError as error:
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                return Result("TIMEOUT", None)
            return Result("UNAVAILABLE", None)
