#!/usr/bin/env python3
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge-dir", required=True)
    parser.add_argument("--solution-file", required=True)
    parser.add_argument("--flag", default="")
    args = parser.parse_args()
    print(json.dumps(verify(args.challenge_dir, args.solution_file, args.flag)))

def verify(challenge_dir, solution_file, flag):
    challenge_path = Path(challenge_dir)
    solution_path = Path(solution_file)
    if not challenge_path.exists():
        return {"solved": False, "challenge_address": "", "message": "Challenge dir not found"}
    if not solution_path.exists():
        return {"solved": False, "challenge_address": "", "message": "Solution file not found"}
    try:
        return _do_verify(challenge_path, solution_path, flag)
    except subprocess.TimeoutExpired:
        return {"solved": False, "challenge_address": "", "message": "Verification timed out"}
    except Exception as e:
        return {"solved": False, "challenge_address": "", "message": str(e)}

TEST_CODE = r"""
#[test_only]
module challenge::verify {
    use challenge::challenge;
    use solution::solve;
    use sui::tx_context;

    #[test]
    fun test_solve() {
        let ctx = tx_context::dummy();
        let chal = challenge::initialize(&mut ctx);
        solve::solve(&mut chal, &mut ctx);
        assert!(challenge::is_solved(&chal), 0);
        challenge::destroy(chal);
    }
}
"""

def _do_verify(challenge_dir, solution_file, flag):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for item in challenge_dir.iterdir():
            if item.name in ("build", "Move.lock"):
                continue
            dst = tmp / item.name
            (shutil.copytree if item.is_dir() else shutil.copy2)(item, dst)
        shutil.copy2(solution_file, tmp / "sources" / "solve.move")
        (tmp / "sources" / "verify.move").write_text(TEST_CODE)

        move_toml = tmp / "Move.toml"
        content = move_toml.read_text()
        # Strip explicit Sui deps (newer CLI auto-adds them)
        lines = []
        skip = False
        for line in content.split("\n"):
            if line.strip().startswith("[dependencies]"):
                skip = True
                continue
            if skip and line.startswith("["):
                skip = False
            if not skip:
                lines.append(line)
        content = "\n".join(lines)
        if "[addresses]" in content:
            content += "\nsolution = \"0x0\"\n"
        else:
            content += "\n[addresses]\nsolution = \"0x0\"\n"
        move_toml.write_text(content)

        build = subprocess.run(
            ["sui", "move", "build", "--path", str(tmp)],
            capture_output=True, text=True, timeout=120
        )
        if build.returncode != 0:
            return {"solved": False, "message": "Build failed:\n" + build.stderr[:2000]}

        test = subprocess.run(
            ["sui", "move", "test", "--path", str(tmp)],
            capture_output=True, text=True, timeout=120
        )
        if test.returncode == 0:
            return {"solved": True, "message": "Congrats, flag: " + flag}
        return {"solved": False, "message": "Test failed:\n" + test.stdout[:1000] + "\n" + test.stderr[:1000]}

if __name__ == "__main__":
    main()
