"""Publish the complete 1.7B comparison independently of the 4B process lifecycle."""
import json
import time
from extend_4b_wait import RUN, primary_done, publish_primary, read


def main():
    receipt = RUN / "primary_watcher.json"
    while True:
        if primary_done():
            code = publish_primary()
            receipt.write_text(json.dumps({"status": "DONE" if code == 0 else "FAILED",
                "analysis_exit_code": code, "ended_unix": time.time()}) + "\n")
            return
        failures = []
        for label in ("1p7_control", "1p7_mixed"):
            for path in (RUN / "execution" / label).glob("*.json"):
                if read(path).get("status") == "FAILED":
                    failures.append(str(path))
        if failures:
            receipt.write_text(json.dumps({"status": "BLOCKED_PRIMARY_FAILURE", "failed_receipts": failures,
                "checked_unix": time.time()}) + "\n")
            return
        receipt.write_text(json.dumps({"status": "WAITING", "checked_unix": time.time()}) + "\n")
        time.sleep(30)


if __name__ == "__main__":
    main()
