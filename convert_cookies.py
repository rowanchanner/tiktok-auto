"""Convert Netscape cookie .txt to JSON for tiktokautouploader."""
import json, sys

if len(sys.argv) < 3:
    print("Usage: python convert_cookies.py cookies.txt username")
    sys.exit(1)

cookies = []
with open(sys.argv[1]) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            cookies.append({
                "domain": parts[0],
                "path": parts[2],
                "secure": parts[3] == "TRUE",
                "expires": int(parts[4]) if parts[4] != "0" else -1,
                "name": parts[5],
                "value": parts[6],
            })

out = f"CookieFile{sys.argv[2]}.json"
with open(out, "w") as f:
    json.dump(cookies, f, indent=2)
print(f"Saved {len(cookies)} cookies to {out}")
