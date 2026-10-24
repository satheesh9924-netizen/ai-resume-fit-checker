"""Poll for an outcome with a timeout instead of sleeping for a fixed time."""
import time


def wait_until(condition, timeout=30.0, interval=0.5, message="condition was not met"):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            if condition():
                return
        except Exception as error:  # service may still be starting; keep polling
            last_error = error
        time.sleep(interval)
    detail = f" (last error: {last_error})" if last_error else ""
    raise AssertionError(f"{message} within {timeout}s{detail}")
