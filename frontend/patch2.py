import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace handleExtractBooking catch block
pattern_extract = re.compile(r"catch \(err\) \{\s*console.error\(\"Extraction error:\", err\);\s*setImportError\(err.message \|\| 'Failed to extract booking'\);\s*\}")
replacement_extract = """catch (err) {
        console.error("Extraction error:", err);
        if (err.message === "Failed to fetch") {
          setImportError("Unable to connect to the agent server.");
        } else if (err.message.includes("400") || err.message.includes("422")) {
          setImportError("The provided document is invalid or empty.");
        } else if (err.message.includes("500") || err.message.includes("extract")) {
          setImportError("The AI agent failed to process the document.");
        } else {
          setImportError(err.message || 'Failed to extract booking');
        }
      }"""
content = pattern_extract.sub(replacement_extract, content)


# In handleImportTextSubmit, it sets importStatus instead of importError, and logs to console.
# We need to change handleImportTextSubmit to match the exact requirement if we want to show it there, but for now the user mentioned the error "Failed to fetch" showing up which only happens where importError is set. Wait, let's also update handleFileChange catch block.
pattern_file = re.compile(r"catch \(err\) \{\s*console.error\(\"Import error:\", err\);\s*setImportError\(err.message \|\| 'Failed to process import'\);\s*\}")
replacement_file = """catch (err) {
      console.error("Import error:", err);
      if (err.message === "Failed to fetch") {
        setImportError("Unable to connect to the agent server.");
      } else if (err.message.includes("400") || err.message.includes("422")) {
        setImportError("The provided document is invalid or empty.");
      } else if (err.message.includes("500") || err.message.includes("extract")) {
        setImportError("The AI agent failed to process the document.");
      } else {
        setImportError(err.message || 'Failed to process import');
      }
    }"""
content = pattern_file.sub(replacement_file, content)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched errors successfully")
