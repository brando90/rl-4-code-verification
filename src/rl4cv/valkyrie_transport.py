"""Select hosted Valkyrie or explicit legacy transport without migrating historical runs implicitly."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess


PROVIDER_ENV = {
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "MODEL_GATEWAY_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN",
    "PYTHONPATH", "PYTHONHOME", "AUTH_DISABLED", "TRACKER_SERVICE_URL",
}


class Transport:
    """Hosted is the default; legacy requires both an explicit mode and executable."""

    def __init__(self, legacy_config: Path):
        self.mode = os.environ.get("RL4CV_VALKYRIE_TRANSPORT", "hosted")
        if self.mode not in {"hosted", "legacy"}:
            raise ValueError("RL4CV_VALKYRIE_TRANSPORT must be hosted or legacy")
        self.config = legacy_config
        self._hosted_identity = None
        self._credential = None
        self.binary = os.environ.get("VALKYRIE_BIN")
        if not self.binary:
            if self.mode == "legacy":
                raise ValueError("Legacy transport requires VALKYRIE_BIN pointing to the retained legacy CLI")
            self.binary = shutil.which("valkyrie-hosted") or "valkyrie"

    def env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
        for key in ("VALKYRIE_ENV", "VALKYRIE_CONFIG_PATH"):
            env.pop(key, None)
        if self.mode == "legacy":
            env.pop("VALKYRIE_API_KEY", None)
            env.pop("VALKYRIE_URL", None)
            env.update(VALKYRIE_ENV="bench", VALKYRIE_CONFIG_PATH=str(self.config))
        return env

    def run(self, args: list[str], *, timeout: float = 600, value: str | None = None):
        kwargs = {"input": value} if value is not None else {"stdin": subprocess.DEVNULL}
        return subprocess.run([self.binary, *args], env=self.env(), capture_output=True,
                              text=True, timeout=timeout, **kwargs)

    def checked(self, args: list[str], *, value: str | None = None) -> str:
        result = self.run(args, value=value)
        if result.returncode:
            # Do not echo subprocess output: even a failing external client may reflect stdin.
            raise RuntimeError(f"Valkyrie {' '.join(args[:3])} failed (exit {result.returncode}); no automatic retry")
        return result.stdout

    def preflight(self, *, registration: bool = False) -> None:
        if self.mode == "hosted":
            identity = self.checked(["whoami"])
            # Pinned 865135f CLI format. Resolve the actual saved-login Tracker and
            # organization, since VALKYRIE_URL alone need not select either one.
            found = re.search(r" in (.+) on (https?://\S+) \(using (a login|an access key)\)\s*$", identity)
            if not found:
                raise RuntimeError("Unrecognized Valkyrie whoami format; cannot bind route identity")
            organization, url, self._credential = found.groups()
            self._hosted_identity = {"organization": organization, "tracker_url": url.rstrip("/")}
            if registration and self._credential != "a login":
                raise RuntimeError("Service registration needs valkyrie login; unset VALKYRIE_API_KEY if it overrides the login")
            self.checked(["provider", "list"])
        elif not self.config.is_file():
            raise RuntimeError(f"Legacy configuration missing: {self.config}")

    def identity(self) -> dict[str, str]:
        out = {"transport": self.mode, "valkyrie_bin": self.binary}
        if self.mode == "legacy":
            out["valkyrie_config"] = str(self.config)
        else:
            if self._hosted_identity is None:
                self.preflight()
            out.update(self._hosted_identity)
        return out

    def require_receipt(self, receipt: dict) -> None:
        recorded = receipt.get("transport", "legacy")
        if recorded != self.mode:
            raise RuntimeError(f"Receipt belongs to {recorded} transport; select that transport explicitly for historical access")
        if self.mode == "hosted":
            current = self.identity()
            if any(receipt.get(k) != current[k] for k in ("tracker_url", "organization")):
                raise RuntimeError("Receipt Tracker or organization differs from the authenticated route; restore its original selection")

    def register(self, benchmark: str, url: str, bearer: Path, host_config: Path) -> dict:
        """Store only the selected service; the credential never enters argv or a receipt."""
        header = "Bearer " + bearer.read_text().strip()
        if self.mode == "hosted":
            secret = benchmark + "-service-auth"
            if not re.fullmatch(r"[A-Za-z0-9_+=.@-]{1,128}", secret):
                raise ValueError("Benchmark does not produce a valid hosted service secret name")
            self.preflight(registration=True)
            self.checked(["secret", "set", secret], value=header)
            self.checked(["benchmark", "service", "set", benchmark, url,
                          "--auth-secret", secret, "--auth-header", "Authorization"])
            return {**self.identity(), "auth_secret": secret, "auth_header": "Authorization"}
        import yaml
        source = self.config if self.config.exists() else host_config
        cfg = yaml.safe_load(source.read_text()) or {}
        cfg.setdefault("custom_benchmark_services", {})[benchmark] = url
        cfg.setdefault("benchmark_auth", {})[benchmark] = header
        self.config.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Open with owner-only mode even when the caller's umask is permissive.
        fd = os.open(self.config, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(yaml.safe_dump(cfg))
        return self.identity()

    def endpoint(self, benchmark: str, private: Path) -> tuple[str, str]:
        if self.mode == "legacy":
            import yaml
            cfg = yaml.safe_load(self.config.read_text())
            return cfg["custom_benchmark_services"][benchmark], cfg["benchmark_auth"][benchmark]
        matches = []
        for path in private.glob("deployment*.json"):
            receipt = json.loads(path.read_text())
            if receipt.get("benchmark") == benchmark and not receipt.get("torn_down_utc"):
                self.require_receipt(receipt)
                matches.append(receipt)
        if len(matches) != 1:
            raise RuntimeError("Need exactly one current hosted deployment receipt for the requested benchmark")
        receipt = matches[0]
        return receipt["tunnel_url"], "Bearer " + Path(receipt["bearer_file"]).read_text().strip()
