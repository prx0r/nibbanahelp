#!/usr/bin/env python3
"""sync_r2.py — pull live edits from R2 into the repo, then republish.

  python3 tools/sync_r2.py

Reads nibbanahelp-live/pending/* (bodies saved from the live /save form),
applies them to repo files (headers preserved), deletes the R2 keys,
commits + pushes, rebuilds the static page + worker bundle, redeploys.
Stdlib + boto3 (creds from /root/.r2-env).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ALLOWED = re.compile(r"^(entries|essays|tensions)/[^/]+\.md$|^motto\.txt$")

ROOT = Path(__file__).resolve().parent.parent


def sh(*args):
    r = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", args, r.stderr[-500:])
        sys.exit(1)
    return r.stdout.strip()


def main():
    import boto3
    env = {}
    with open("/root/.r2-env") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    s3 = boto3.client("s3", endpoint_url=env["R2_ENDPOINT"],
                      aws_access_key_id=env["R2_ACCESS_KEY"],
                      aws_secret_access_key=env["R2_SECRET_KEY"])
    B = "nibbanahelp-live"
    pg = s3.get_paginator("list_objects_v2")
    keys = [o["Key"] for page in pg.paginate(Bucket=B, Prefix="pending/")
            for o in page.get("Contents", [])]
    if not keys:
        print("nothing pending")
        return
    applied = []
    for key in keys:
        f = key[len("pending/"):]
        if not ALLOWED.match(f):
            print("skip (not allowed):", f)
            continue
        body = s3.get_object(Bucket=B, Key=key)["Body"].read().decode()
        p = ROOT / f
        if not p.is_file():
            print("skip (not in repo):", f)
            continue
        text = p.read_text()
        head = text.split("---", 1)[0] + "---\n" if "---" in text else ""
        p.write_text(head + body.rstrip() + "\n")
        s3.delete_object(Bucket=B, Key=key)
        applied.append(f)
        print("applied:", f)
    if not applied:
        return
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m",
       f"sync live edits ({len(applied)} files)")
    sh("git", "push", "-q", "origin", "main")
    sh("python3", "tools/site.py")
    sh("node", "worker/build.mjs")
    env = dict(**os.environ)
    env["CLOUDFLARE_API_TOKEN"] = open("/root/.cf-api-token").read().strip()
    subprocess.run(["wrangler", "deploy"], cwd=str(ROOT / "worker"),
                   capture_output=True, text=True, env=env, timeout=180)
    print("rebuilt + redeployed")


if __name__ == "__main__":
    main()
