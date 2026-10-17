import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the closing tags at the end of renderTrips
content = content.replace(
    "        )}\n      </div>\n    </div>\n  );",
    "        )}\n      </main>\n    </div>\n  );"
)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched main tag successfully")
