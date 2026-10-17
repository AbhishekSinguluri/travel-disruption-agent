import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
    r"const res = await fetch\('http://localhost:8000/api/bookings/extract', \{\s*"
    r"method: 'POST',\s*"
    r"headers: \{ 'Content-Type': 'application/json' \},\s*"
    r"body: JSON\.stringify\(\{ type: 'text', text: importText \}\)\s*"
    r"\}\);"
)

replacement = """const fd = new FormData();
        fd.append('text', importText);
        const res = await fetch('http://localhost:8000/api/bookings/extract', {
          method: 'POST',
          body: fd
        });"""

content = pattern.sub(replacement, content)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched App.jsx successfully.")
