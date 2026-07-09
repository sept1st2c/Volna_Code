import os

import httpx

# Public Piston API went whitelist-only (Feb 2026). Self-hosted via Docker:
#   docker run -d --name piston_api --privileged -p 2000:2000 \
#     -v ./.piston-data/packages:/piston/packages --tmpfs /piston/jobs:exec \
#     -e PISTON_OUTPUT_MAX_SIZE=131072 -e PISTON_MAX_FILE_SIZE=10000000 \
#     ghcr.io/engineer-man/piston
# Python 3.10.0 package installed via the Piston CLI after the container is up.
# PISTON_OUTPUT_MAX_SIZE matters: Piston's default stdio buffer is 1024 bytes,
# which truncates mid-write and manifests as "Sandbox keeper received fatal
# signal 6" with empty stdout even though the real cause is status "OL"
# (output limit), not a sandbox crash.
PISTON_URL = os.environ.get("PISTON_URL", "http://localhost:2000/api/v2/execute")
PYTHON_VERSION = "3.10.0"


class PistonError(Exception):
    pass


async def run_python(source: str, timeout_s: float = 15.0) -> dict:
    """Submit source to Piston and return the raw run result (stdout/stderr/code)."""
    payload = {
        "language": "python",
        "version": PYTHON_VERSION,
        "files": [{"content": source}],
        "run_timeout": 3000,
    }
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.post(PISTON_URL, json=payload)
    if resp.status_code != 200:
        raise PistonError(f"Piston returned HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    run = data.get("run", {})
    compile_ = data.get("compile")
    if compile_ and compile_.get("code") not in (0, None):
        raise PistonError(f"Compile error: {compile_.get('stderr') or compile_.get('output')}")
    return run
