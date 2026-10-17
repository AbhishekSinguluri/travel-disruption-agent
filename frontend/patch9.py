import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix handleImport to dynamically set accept before clicking
old_handleImport = """  const handleImport = (type) => {
    setImportFileType(type);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
      fileInputRef.current.click();
    }
  };"""

new_handleImport = """  const handleImport = (type) => {
    setImportFileType(type);
    if (fileInputRef.current) {
      fileInputRef.current.accept = type === 'pdf' ? '.pdf' : 'image/*';
      fileInputRef.current.value = null;
      fileInputRef.current.click();
    }
  };"""

content = content.replace(old_handleImport, new_handleImport)

# Also make sure "Upload PDF" is visible in TRIP mode too!
# In my code:
#                       {monitoringMode === 'BOOKINGS' && (
#                         <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>
#                       )}
old_pdf_btn = """                      {monitoringMode === 'BOOKINGS' && (
                        <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>
                      )}"""

new_pdf_btn = """                      <button onClick={() => handleImport('pdf')} disabled={importing} className="bg-[#F9F8F6] border border-slate-200 text-slate-800 px-6 py-3 rounded-full text-sm font-medium hover:bg-white transition-all shadow-sm">Upload PDF</button>"""

content = content.replace(old_pdf_btn, new_pdf_btn)

with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 9 applied.")
