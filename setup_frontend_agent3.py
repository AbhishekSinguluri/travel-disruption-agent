import re

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add activeStopId state
if "const [activeStopId, setActiveStopId]" not in content:
    content = re.sub(
        r'(export default function App\(\) \{\n)',
        r'\1  const [activeStopId, setActiveStopId] = useState(null);\n',
        content
    )

# 2. Update MapComponent props
if "activeStopId={activeStopId}" not in content:
    content = re.sub(
        r'(<MapComponent\s*\n\s*stops=\{stops\})',
        r'\1\n                    activeStopId={activeStopId}\n                    onStopClick={setActiveStopId}',
        content
    )

# 3. Add onClick to timeline stops
if "onClick={() => setActiveStopId(stop.id)}" not in content:
    content = re.sub(
        r'(<div key=\{stop\.id\} className="relative"([^>]*)>)',
        r'\1 onClick={() => setActiveStopId(stop.id)} style={{cursor: "pointer"}}>',
        content
    )
    
# 4. Highlight timeline stop if active
if "bg-blue-50" not in content and "bg-slate-100" not in content and "activeStopId === stop.id" not in content:
    content = re.sub(
        r'(<div className={`absolute -left-\[29px\] w-4 h-4 rounded-full border-\[3px\] border-\[#F9F8F6\] \n\$\{stop\.status === \'REPLACED\' \? \'bg-emerald-500\' : stop\.completed \? \'bg-blue-600\' : \'bg-slate-800\'\}`\}></div>)',
        r'\1\n                      {activeStopId === stop.id && <div className="absolute inset-0 bg-blue-50/50 rounded-xl -left-4 -right-4 -top-2 -bottom-2 -z-10"></div>}',
        content
    )

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(content)

# 5. Update MapComponent.jsx to use activeStopId
with open("frontend/src/components/MapComponent.jsx", "r", encoding="utf-8") as f:
    map_content = f.read()

if "activeStopId" not in map_content:
    map_content = map_content.replace(
        "affectedStopId, candidates = [], selectedCandidateId, currentLocation }",
        "affectedStopId, candidates = [], selectedCandidateId, currentLocation, activeStopId, onStopClick }"
    )
    map_content = map_content.replace(
        "<Marker key={stop.id} position={[stop.latitude, stop.longitude]} icon={stop.id === affectedStopId ? redIcon : blueIcon}>",
        "<Marker key={stop.id} position={[stop.latitude, stop.longitude]} icon={stop.id === affectedStopId ? redIcon : (stop.id === activeStopId ? greenIcon : blueIcon)} eventHandlers={{ click: () => onStopClick && onStopClick(stop.id) }}>"
    )
    with open("frontend/src/components/MapComponent.jsx", "w", encoding="utf-8") as f:
        f.write(map_content)

print("Frontend agents setup complete.")
