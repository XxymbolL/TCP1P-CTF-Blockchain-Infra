import json
import os

import sandbox
from sandbox.sui_helper import call_function, get_object_id_by_type, publish_package

CHALLENGE_PACKAGE_PATH = os.getenv("SUI_CHALLENGE_PACKAGE", "/home/ctf/setup")


def deploy(rpc_url: str, admin_client_config: str, admin_address: str, player_address: str) -> str:
    package_id = publish_package(admin_client_config, CHALLENGE_PACKAGE_PATH)

    call_function(admin_client_config, package_id, "challenge", "initialize")

    challenge_object_id = get_object_id_by_type(
        rpc_url, admin_address, package_id, "challenge", "Challenge"
    )

    if not challenge_object_id:
        raise RuntimeError("Could not find Challenge object after initialization")

    return json.dumps({"package_id": package_id, "challenge_object_id": challenge_object_id})


app = sandbox.run_launcher(deploy)
