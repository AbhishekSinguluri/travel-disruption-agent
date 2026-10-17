import re

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We need to find the start and end indices of the `!showImportModal` block.
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "<main className=\"max-w-7xl mx-auto px-8 py-16 relative\">" in line:
        start_idx = i
    if "        ) : (" in line and start_idx != -1 and i > start_idx:
        # Check if the next line is `<motion.div`
        if i + 1 < len(lines) and "<motion.div" in lines[i+1]:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing lines {start_idx} to {end_idx-1}")
    
    # We will extract the exact code for the Monitor panels and Trips list from the file to preserve it perfectly.
    monitor_panel_code = ""
    trips_list_code = ""
    
    in_monitor = False
    in_trips = False
    for i in range(start_idx, end_idx):
        if 'className="flex gap-4"' in lines[i] and 'mb-16' not in lines[i] and not in_monitor:
            in_monitor = True
            monitor_panel_code += '                <div className="flex gap-4 mb-16">\n'
            continue
        
        if in_monitor:
            if 'className="hidden md:block w-1/2 relative h-[500px] z-10 translate-x-[30px]"' in lines[i]:
                in_monitor = False
            elif 'className="flex flex-col gap-8"' in lines[i]:
                in_monitor = False
            else:
                monitor_panel_code += lines[i]
                
    for i in range(start_idx, end_idx):
        if 'className="flex flex-col gap-8"' in lines[i] and not in_trips:
            in_trips = True
        
        if in_trips:
            # wait, how do we know when trips list ends?
            # It ends when we hit the closing tag before `</>`
            trips_list_code += lines[i]
            
    # However, in_trips will capture the `</div>` and `</>` and everything.
    # Let's just manually read the file and extract it.
    
else:
    print("Could not find start or end index!")
