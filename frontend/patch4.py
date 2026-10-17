import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# First we need to make sure the div opened at line 469 closes.
# It is currently unclosed because we replaced the inner div closing tag.
# We'll just look for `              )}\n            </div>\n          </>\n        ) : (`
# and add an extra `</div>` there.

content = content.replace(
    "              )}\n            </div>\n          </>\n        ) : (",
    "              )}\n            </div>\n            </div>\n          </>\n        ) : ("
)

# And we also need to close `<main>` before the last `</div>` of renderTrips.
# wait, where is the last `</div>` of renderTrips?
# Line 765 is `</motion.div>`, 766 is `)}`, 767 is `</div>`, 768 is `</div>`.
# The first `</div>` at 767 closes `className="flex flex-col md:flex-row gap-16 items-center"`
# Wait, NO! 
# Let's just fix the `div` in the true branch of `!showImportModal`.

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched closing tag successfully")
