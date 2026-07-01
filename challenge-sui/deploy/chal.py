import json
import os
import shutil
import tempfile

import sandbox
from sandbox.sui_helper import call_function, find_created_object, publish_package

CHALLENGE_PACKAGE_PATH = os.getenv("SUI_CHALLENGE_PACKAGE", "/home/ctf/setup")


def deploy(rpc_url: str, admin_client_config: str, admin_address: str, player_address: str) -> str:
    tmp = tempfile.mkdtemp(prefix="sui-publish-")
    tmp_pkg = os.path.join(tmp, "pkg")
    shutil.copytree(
        CHALLENGE_PACKAGE_PATH, tmp_pkg,
        ignore=shutil.ignore_patterns("Pub.local.toml", "build", ".move"),
    )

    package_id = publish_package(admin_client_config, tmp_pkg)

    init_result = call_function(admin_client_config, package_id, "challenge", "initialize")
    challenge_object_id = find_created_object(init_result)

    shutil.rmtree(tmp, ignore_errors=True)

    if not challenge_object_id:
        raise RuntimeError("Could not find Challenge object after initialization")

    return json.dumps({"package_id": package_id, "challenge_object_id": challenge_object_id})


app = sandbox.run_launcher(deploy)
