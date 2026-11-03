#!/usr/bin/env python3
"""Verify the built Plik LPK. Assertions run with comments stripped."""
import hashlib
import os
import re
import subprocess
import sys
import tarfile

LPK = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pk.lpk"
EXTRACT = "/tmp/pkx"
fail = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fail.append(msg)


with tarfile.open(LPK) as tf:
    names = tf.getnames()
print("LPK entries:", names)
for required in ["manifest.yml", "package.yml", "deploy_params.yml", "icon.png", "content.tar"]:
    check(required in names, f"archive contains {required}")

sha = hashlib.sha256(open(LPK, "rb").read()).hexdigest()
print("LPK sha256:", sha)
check(len(sha) == 64, "sha256 computed")

os.makedirs(EXTRACT, exist_ok=True)
subprocess.run(["tar", "xf", LPK, "-C", EXTRACT], check=True)
raw = open(os.path.join(EXTRACT, "manifest.yml")).read()
pkg = open(os.path.join(EXTRACT, "package.yml")).read()
body = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))

check("community.lazycat.app.plik" in pkg, "package id is plik")
check("1.5.0" in pkg, "min_os_version 1.5.0")
m = re.search(r"^version:\s*(\S+)", pkg, re.M)
ver = m.group(1) if m else ""
print("package version:", ver)
check([int(x) for x in ver.split(".")] == [1, 4, 3], "package version is 1.4.3")
check("MIT" in pkg, "license MIT")

check("subdomain: plik" in body, "subdomain set")
# upstream ships with auth disabled, so it stays behind the platform entry
check(re.search(r"^\s*public_path:", body, re.M) is None,
      "no public_path key (auth disabled upstream; stays behind platform entry)")
check("backend: http://plik:8080/" in body, "upstream points at plik:8080")
check("docker.1ms.run/rootgg/plik:1.4.3" in body, "image pinned 1.4.3")

binds = [l.strip()[2:] for l in body.splitlines() if l.strip().startswith("- /lzcapp/")]
print("binds:", binds)
check(any("/lzcapp/var:/lzcapp/var" in b for b in binds), "data dir persisted")
check(all("docker.sock" not in b for b in binds), "no docker.sock bind")
check("network_mode" not in body, "no host network mode")
check("privileged" not in body, "no privileged flag")

blocks = []
for chunk in body.split("environment:")[1:]:
    vals = []
    for line in chunk.splitlines():
        s = line.strip()
        if s.startswith("- "):
            vals.append(s[2:])
        elif s == "":
            continue
        else:
            break
    blocks.append(vals)
env = blocks[0] if blocks else []
print("env:", [v.split("=")[0] for v in env])

# storage + metadata must both point inside the persisted volume
data = [v for v in env if v.startswith("PLIKD_DATA_BACKEND_CONFIG=")]
meta = [v for v in env if v.startswith("PLIKD_METADATA_BACKEND_CONFIG=")]
check(bool(data) and "/lzcapp/var/files" in data[0], "file storage points at the persisted volume")
check(bool(meta) and '"Driver":"sqlite3"' in meta[0], "metadata backend is sqlite")
check(bool(meta) and "/lzcapp/var/db/plik.db" in meta[0], "sqlite db points at the persisted volume")
check("PLIKD_ASSUME_HTTPS=false" in env, "ASSUME_HTTPS false (entry terminates TLS)")
check(any(v.startswith("PLIKD_SOURCE_IP_HEADER=") for v in env), "source IP header set for proxy")

check("docker.1ms.run/" in body, "image rewritten to mirror registry")
check("未做真机验证" in raw or "未在设备上实测" in raw, "usage states untested")
check("默认" in raw and "匿名" in raw, "usage explains the anonymous-by-default nature")

print()
if fail:
    print("FAILED:", len(fail))
    for f in fail:
        print(" -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
