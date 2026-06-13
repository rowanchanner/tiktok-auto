import os
import site

def patch():
    # Get all possible site-packages directories
    site_packages = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        site_packages.append(site.getusersitepackages())
        
    for sp in site_packages:
        function_py = os.path.join(sp, 'tiktokautouploader', 'function.py')
        if os.path.exists(function_py):
            with open(function_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix Playwright strict mode violation for Cancel buttons
            content = content.replace('"button:has-text(\'Cancel\')"', '"button:has-text(\'Cancel\') >> nth=0"')
            content = content.replace("'button:has-text(\\'Cancel\\')'", "'button:has-text(\\'Cancel\\') >> nth=0'")
            
            with open(function_py, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully patched {function_py}")
            return

    print("Could not find tiktokautouploader in site-packages!")

if __name__ == "__main__":
    patch()
