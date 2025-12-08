# Copilot Instructions for MASI V2025 Intern Test

## Project Goal: Urban Design 3D City Dashboard with LLM Querying

**Objective**: Build a web-based 3D city dashboard that visualizes Calgary building data and uses an LLM to interpret natural language queries for filtering.

**Key Requirements**:
1. Fetch 3-4 city blocks of Calgary building data (footprints, heights, zoning, property values)
2. Visualize buildings in 3D using Three.js with extruded shapes based on actual data
3. Interactive clicks highlight buildings and show popup details
4. LLM integration: Users query in natural language (e.g., "buildings over 100 feet"), LLM parses intent, backend filters, frontend highlights results
5. Deliver UML diagram + README with setup instructions + hosted public link
6. **Time limit**: 24 hours

## Architecture Overview

This is a full-stack application with a **React frontend** and **Flask backend**:

- **Frontend** (`map/`): React app using `react-scripts` + Three.js, proxies API requests to `http://127.0.0.1:5000`
- **Backend** (`backend/`): Flask server handling data fetching, LLM integration, and filtering
- **External APIs**:
  - **Building Data**: City of Calgary Open Data (e.g., property assessments, zoning, building footprints)
  - **LLM**: Hugging Face Inference API (free tier) for query interpretation

### Data Flow
1. Frontend: User types natural language query in text input
2. React sends query to Flask `/query` endpoint
3. Flask sends query to Hugging Face LLM with structured prompt: `"Extract filter from query: {user_input}. Return JSON: {attribute, operator, value}"`
4. LLM returns parsed filter (e.g., `{"attribute": "height", "operator": ">", "value": 100}`)
5. Flask applies filter to building dataset, returns matching building IDs
6. React/Three.js highlights matching buildings (color change), dims others
7. Click on building shows popup with details (address, height, zoning, assessed value, etc.)

## Setup & Development Workflow

### Prerequisites
- **Node.js** (v16+): Frontend and npm
- **Python** (v3.8+): Backend
- **Hugging Face API Key**: Already configured in `backend/.env` as `HF_TOKEN`
- **Calgary Open Data API**: Data fetched via SODA API (`soda-js` library)

### Development Commands

#### Frontend (`map/` directory)
```bash
npm start          # Dev server on localhost:3000, proxies to backend:5000
npm test           # Run Jest tests in watch mode
npm run build      # Production build (minified, hashed filenames)
```

#### Backend (`backend/` directory)
```bash
python3 server.py   # Runs Flask dev server (debug=True, port 5000)
                    # HF_TOKEN loaded from .env file automatically
```

**Critical**: Both must run simultaneously. React's proxy (in `package.json`) routes `/api/*` requests to `http://127.0.0.1:5000/api/*`

## Key Files & Implementation Plan

| File | Purpose | Status |
|------|---------|--------|
| `map/src/App.js` | Main React component with 3D viewer (Three.js) and query input | Three.js imported, SODA consumer initialized |
| `map/src/components/ThreeViewer.js` | Three.js scene setup, building meshes, mouse picking | To build |
| `map/src/components/QueryPanel.js` | Text input for natural language queries, result display | To build |
| `map/src/services/api.js` | Fetch `/api/buildings`, `/api/query` endpoints | To build |
| `backend/server.py` | Flask routes: `/api/buildings`, `/api/query`, LLM integration | Basic structure exists |
| `backend/data_fetcher.py` | Fetch Calgary open data (building footprints, heights, zoning, assessed values) | To build |
| `backend/llm_processor.py` | Query Hugging Face API, parse LLM response to structured filter | To build |
| `backend/.env` | Environment variables (HF_TOKEN for Hugging Face API) | ✅ Configured |
| `docs/UML.pdf` | Class + sequence diagrams for architecture | To create |

## Implementation Strategy

### Phase 1: Data Pipeline (Backend)
1. **Fetch Calgary building data**: Use both SODA API endpoints already configured
   - **Building Footprints/Heights**: `https://data.calgary.ca/resource/cchr-krqg.json` (initialized in `App.js`)
     - Key fields: `polygon` (Polygon GeoJSON), `rooftop_elev_z`, `grd_elev_min_z`, `struct_id`
   - **Property Assessment Data**: `https://data.calgary.ca/resource/4bsw-nn7w.json` (Socrata client in `server.py`)
     - Key fields: `multipolygon` (MultiPolygon GeoJSON), `address`, `assessed_value`, `land_use_designation`, `year_of_construction`
   - **Target Area** (4 blocks defined in `App.js`):
     - Top left: `51.03999458794443, -114.07919451901128`
     - Top right: `51.03982364829675, -114.07429304853973`
     - Bottom left: `51.03902424569097, -114.07927447774654`
     - Bottom right: `51.03893877415592, -114.074373007275`
2. **Create `data_fetcher.py`**: Combine data from both endpoints, extract: `{id, address, lat, lon, footprint_coords, height, zoning, assessed_value}`
   - Filter data to only buildings within the bounding box above
   - **Join method**: Match buildings by comparing `polygon` (footprint DB) with `multipolygon` (property DB) using geometry intersection
     - Both use GeoJSON format with coordinates as `[longitude, latitude]` (note: reversed from typical lat/lon order)
     - Use `intersects()` function or compare coordinate overlap to match same building across datasets
     - Calculate height as `rooftop_elev_z - grd_elev_min_z`
3. **Create `/api/buildings` endpoint**: Returns full dataset as JSON array

### Phase 2: LLM Query Processor (Backend)
1. **Create `llm_processor.py`**: Query Hugging Face API with structured prompt
   - Prompt: `"Extract filter conditions from user query: '{user_query}'. Return ONLY valid JSON: {{attribute: string, operator: '>' | '<' | '==' | 'contains', value: any}}"`
   - Handle responses: validate JSON, map attribute names to dataset fields
2. **Create `/api/query` endpoint**: Accept `{query: string}`, return `{matching_ids: [id1, id2, ...]}`

### Phase 3: 3D Visualization (Frontend)
1. **Create `ThreeViewer.js`**: Three.js scene with:
   - Floor plane (gray background)
   - Extruded buildings (light color) with lat/lon → 3D coordinates mapping
   - Raycaster for mouse picking
   - State: `{selectedBuildingId, highlightedBuildingIds}`
2. **Building interaction**: Click → highlight (color change) + show popup with details
3. **Query results**: Call `/api/query`, receive IDs, highlight those buildings, dim others

### Phase 4: Query Integration (Frontend)
1. **Create `QueryPanel.js`**: Text input + submit button
   - On submit: Call `/api/query` endpoint
   - Display: "Found 5 buildings" or filter details
   - Trigger `ThreeViewer` highlight action

### Phase 5: Deployment & Documentation
1. **Host**: Vercel (React) + Heroku/Railway (Flask) or single VPS
2. **Create UML**: Class diagram (components, data models) + sequence diagram (query flow)
3. **Create README**: Setup steps, API key instructions, feature walkthrough

## API Specification

### GET `/api/buildings`
Returns all buildings in the dataset.
```json
[
  {
    "id": "12345",
    "struct_id": "12345",
    "address": "123 Main St, Calgary",
    "latitude": 51.0486,
    "longitude": -114.0708,
    "height": 45.5,
    "land_use_designation": "RC-G",
    "assessed_value": 520000,
    "footprint": [[lon, lat], [lon, lat], ...]
  },
  ...
]
```

### POST `/api/query`
Interprets natural language query and returns matching building IDs.
```json
{
  "query": "buildings over 100 feet tall",
  "matching_ids": ["12345", "12367", "12389"],
  "filter_parsed": {"attribute": "height", "operator": ">", "value": 100}
}
```

## Critical Workflows

1. **Local Development**: Start backend first (`python3 server.py`), then frontend (`npm start`)
2. **API Debugging**: Requests from React to `/api/*` are routed via the proxy to `http://127.0.0.1:5000/api/*`
3. **LLM Query Flow**: User query → Hugging Face API → Structured filter → Dataset filter → Building IDs → Frontend highlight
4. **3D Interaction**: Click building → Show details popup; Select filter results → Highlight + dim logic

## Project-Specific Conventions

- **Port Convention**: Flask runs on 5000 (hardcoded in `package.json` proxy), React on 3000
- **Python Command**: Use `python3` (not `python`) for backend commands
- **Environment Variables**: Store API keys in `backend/.env`, access via `os.getenv('HF_TOKEN')`
- **State Management**: Uses React hooks (`useState`, `useEffect`); no Redux yet
- **Testing**: Create React App ESLint config extends `react-app` and `react-app/jest`
- **Coordinate System**: 
  - Calgary APIs use GeoJSON format: coordinates are `[longitude, latitude]` (reversed from typical order)
  - Three.js mapping: X = lon, Y = height, Z = -lat
- **Geometry Matching**: Buildings are matched across datasets by comparing `polygon` (footprint) with `multipolygon` (property assessment) using geometry intersection
- **Building Height**: Calculate as `rooftop_elev_z - grd_elev_min_z` from footprint dataset
- **Building ID**: Use `struct_id` from footprint dataset as primary identifier
- **API Response Format**: Always return `{data, error, message}` for consistency
- **Highlight Logic**: Selected building = bright color; matches = medium color; others = dimmed
- **Dependencies Installed**: `three` (v0.181.2), `soda-js` (v0.2.1), Flask (v3.1.2)

## Common Modifications

- **Add Flask routes**: Edit `backend/server.py`, add `@app.route()` decorated functions
- **Add React components**: Create files in `map/src/components/`
- **Update Three.js scene**: Modify `ThreeViewer.js` geometry or materials
- **Change highlight color**: Update `ThreeViewer.js` material colors (e.g., `0xFF0000` for red)
- **Add dependencies**:
  - React: `npm install <package>` in `map/`, update `map/package.json`
  - Python: Add to `backend/requirements.txt` and `pip install -r requirements.txt`

## Hugging Face Integration Details

**API Key Setup**: Already configured in `backend/.env` as `HF_TOKEN="hf_AKapp..."`

**Example Usage in Python**:
```python
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("HF_TOKEN")
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=api_key,
)
completion = client.chat.completions.create(
    model="moonshotai/Kimi-K2-Instruct-0905",
    messages=[
        {
            "role": "user",
            "content": "Describe the process of photosynthesis." #prompt goes here
        }
    ],
)

print(completion.choices[0].message)
```

**Prompt Engineering**:
```python
PROMPT = """Extract filter conditions from this user query: '{user_query}'
Return ONLY a valid JSON object (no extra text) with these fields:
- attribute: one of [height, land_use_designation, assessed_value, address]
- operator: one of ['>', '<', '==', 'contains']
- value: the filter value (number for height/value, string for land_use_designation/address)

Example: User says "buildings over 100 feet"
Response: {{"attribute": "height", "operator": ">", "value": 100}}

User query: {user_query}
Response JSON:"""
```

**Error Handling**: If LLM fails, return `{matching_ids: [], error: "LLM parsing failed"}`

## Calgary Open Data Resources

- **Building Footprints and Height (for rendering)**: `https://data.calgary.ca/resource/cchr-krqg.json` (configured in `App.js`)
  - Contains: `polygon`, `rooftop_elev_z`, `grd_elev_min_z`, `struct_id`
- **Property Assessment and other data**: `https://data.calgary.ca/resource/4bsw-nn7w.json` (configured in `server.py`)
  - Contains: `multipolygon`, `address`, `assessed_value`, `land_use_designation`, `year_of_construction`
