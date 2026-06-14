import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove login route
content = re.sub(r"@app\.route\('/login'\)[\s\S]*?@app\.route\('/auth'\)[\s\S]*?return redirect\(url_for\('dashboard'\)\)", "", content)

# Remove auth checks
content = re.sub(r"\s*user = session\.get\('user'\)\s*if not user:\s*return redirect\(url_for\('login'\)\)", "", content)
content = re.sub(r"\s*user = session\.get\('user'\)\s*if not user:\s*return \"Unauthorized\", 401", "", content)

# Remove logout route
content = re.sub(r"@app\.route\('/logout'\)[\s\S]*?return redirect\(url_for\('login'\)\)", "", content)

# Remove Authlib import
content = content.replace("from authlib.integrations.flask_client import OAuth\n", "")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
