import re
import shutil
import subprocess
import time

import pytest


DOCKER_COMPOSE_FILE = "docker-compose.yml"


def docker_available():
    return shutil.which("docker") is not None


@pytest.mark.skipif(not docker_available(), reason="docker not available")
def test_compose_boot_and_migrate_exits_zero(tmp_path):
    # Validate compose file
    cfg = subprocess.run(["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "config"], capture_output=True)
    assert cfg.returncode == 0, cfg.stderr.decode(errors="ignore")

    # Start stack
    up = subprocess.run(["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "--build", "-d"], capture_output=True)
    assert up.returncode == 0, up.stderr.decode(errors="ignore")

    # Give services some time to start and for migrate to run
    time.sleep(20)

    ps = subprocess.run(["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "ps", "-a"], capture_output=True, text=True)
    assert ps.returncode == 0, ps.stderr
    out = ps.stdout

    # Check migrate exited 0
    migrate_match = re.search(r"(?m)^\s*.+migrate.+Exited \((\d+)\)", out)
    assert migrate_match, "migrate service not found or not exited yet"
    assert migrate_match.group(1) == "0", f"migrate did not exit 0: {migrate_match.group(1)}"

    # Ensure no other service exited with non-zero
    nonzero = re.findall(r"Exited \((\d+)\)", out)
    nonzero = [int(x) for x in nonzero if int(x) != 0]
    assert not nonzero, f"Some containers exited with non-zero codes: {nonzero}\nFull ps output:\n{out}"

    # Tear down
    down = subprocess.run(["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "--volumes", "--remove-orphans"], capture_output=True)
    assert down.returncode == 0, down.stderr.decode(errors="ignore")
