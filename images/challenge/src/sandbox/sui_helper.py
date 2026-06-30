from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import requests


SUI_GAS_BUDGET = int(10000000)


def publish_package(client_config: str, package_path: str, *, gas_budget: int | None = None) -> str:
    budget = gas_budget or SUI_GAS_BUDGET
    result = subprocess.run(
        [
            "sui", "client", "--client.config", client_config,
            "--json", "test-publish", "--build-env", "local",
            "--gas-budget", str(budget),
            package_path,
        ],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"sui client publish failed: code={result.returncode}: "
            f"stdout={result.stdout[-2000:]} stderr={result.stderr[-2000:]}"
        )
    data = json.loads(result.stdout)
    if "effects" in data and "created" in data["effects"]:
        for obj in data["effects"]["created"]:
            if obj.get("owner") == "Immutable":
                pkg_id = obj["reference"]["objectId"]
                if pkg_id.startswith("0x"):
                    return pkg_id
    if "objectChanges" in data:
        for change in data["objectChanges"]:
            if change.get("type") == "published":
                return change["packageId"]
    raise RuntimeError("could not determine package ID from publish output")


def call_function(
    client_config: str,
    package_id: str,
    module: str,
    function: str,
    *,
    args: list[str] | None = None,
    gas_budget: int | None = None,
) -> str:
    budget = gas_budget or SUI_GAS_BUDGET
    cmd = [
        "sui", "client", "--client.config", client_config,
        "--json", "call",
        "--package", package_id,
        "--module", module,
        "--function", function,
        "--gas-budget", str(budget),
    ]
    if args:
        for a in args:
            cmd.extend(["--args", a])
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(
            f"sui client call failed: {package_id}::{module}::{function}: "
            f"stdout={result.stdout[-2000:]} stderr={result.stderr[-2000:]}"
        )
    return result.stdout.strip()


def get_object_id_by_type(
    rpc_url: str, owner_addr: str, package_id: str, module: str, struct: str
) -> str | None:
    response = requests.post(
        rpc_url,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "suix_getOwnedObjects",
            "params": [
                owner_addr,
                {
                    "filter": {"StructType": f"{package_id}::{module}::{struct}"},
                    "options": {"showType": True},
                },
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    objects = data.get("result", {}).get("data", [])
    if objects:
        return objects[0]["data"]["objectId"]
    return None


def check_solved(rpc_url: str, challenge_object_id: str) -> bool:
    try:
        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sui_getObject",
                "params": [challenge_object_id, {"showContent": True}],
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            return False
        content = data.get("result", {}).get("data", {}).get("content", {})
        fields = content.get("fields", {})
        return fields.get("solved", False) is True
    except Exception:
        return False


def fund_account(faucet_url: str, address: str) -> None:
    response = requests.post(
        faucet_url + "/gas",
        json={"FixedAmountRequest": {"recipient": address}},
        timeout=30,
    )
    response.raise_for_status()


def generate_key() -> dict[str, str]:
    result = subprocess.run(
        ["sui", "keytool", "generate", "ed25519", "--json"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"sui keytool generate failed: {result.stderr}")
    return json.loads(result.stdout)


def write_client_config(path: str, rpc_url: str, active_address: str | None, keystore_path: str) -> None:
    active_line = f'active-address: "{active_address}"' if active_address else "active-address: ~"
    Path(path).write_text(
        "\n".join([
            "---",
            f"keystore:",
            f'  File: {keystore_path}',
            "envs:",
            "  - alias: local",
            f'    rpc: "{rpc_url}"',
            "    ws: ~",
            "    basic_auth: ~",
            "active_env: local",
            active_line,
            "",
        ])
    )


def wait_for_rpc(rpc_url: str, timeout: int = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = requests.post(
                rpc_url,
                json={"jsonrpc": "2.0", "id": 1, "method": "sui_getLatestCheckpointSequenceNumber", "params": []},
                timeout=2,
            )
            if response.ok:
                response.json()
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"sui RPC did not become ready: {rpc_url}")
