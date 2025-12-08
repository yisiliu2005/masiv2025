# UML Diagrams - Urban Design 3D City Dashboard

## 1. CLASS DIAGRAM

### Frontend Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            APP (React Component)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ State:                                                                       │
│  - buildings: Building[]                                                    │
│  - selectedBuildingId: string | null                                        │
│  - highlightedBuildingIds: string[]                                         │
│  - queryText: string                                                        │
│  - queryResults: QueryResult | null                                         │
│  - loading: boolean                                                         │
│  - error: string | null                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Methods:                                                                     │
│  + useEffect(): void  // Load buildings on mount                            │
│  + handleQuery(query: string): Promise<void>                                │
│  + handleBuildingClick(buildingId: string): void                            │
│  + render(): JSX.Element                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ├─────────────────────┬──────────────────────┐
           │                     │                      │
           ▼                     ▼                      ▼
  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────┐
  │  ThreeViewer    │  │   QueryPanel     │  │  Building Details │
  ├─────────────────┤  ├──────────────────┤  ├───────────────────┤
  │ Props:          │  │ Props:           │  │ Props:            │
  │ - buildings[]   │  │ - onQuery()      │  │ - building        │
  │ - selectedId    │  │ - loading        │  │ - onClose()       │
  │ - highlighted[] │  │ Props:           │  ├───────────────────┤
  ├─────────────────┤  │ - queryText      │  │ render():         │
  │ State:          │  │ - onQueryChange()│  │ - Address         │
  │ - scene         │  │ - onSubmit()     │  │ - Height          │
  │ - camera        │  ├──────────────────┤  │ - Zoning          │
  │ - renderer      │  │ Methods:         │  │ - Value           │
  │ - buildings3D[] │  │ + render():      │  │ - Year Built      │
  ├─────────────────┤  │   JSX.Element    │  └───────────────────┘
  │ Methods:        │  └──────────────────┘
  │ + useEffect():  │
  │   void          │
  │ + createScene()│
  │   : THREE.Scene│
  │ + addBuildings()│
  │   : void       │
  │ + highlight()  │
  │   : void       │
  │ + handleClick()│
  │   (raycaster)  │
  │ + animate()    │
  │   : void       │
  └─────────────────┘
```

### Data Models

```
┌──────────────────────────────────┐
│        Building                  │
├──────────────────────────────────┤
│ - id: string                     │
│ - struct_id: string              │
│ - address: string                │
│ - latitude: number               │
│ - longitude: number              │
│ - height: number                 │
│ - land_use_designation: string   │
│ - assessed_value: number         │
│ - year_of_construction: string   │
│ - footprint: [lon, lat][][]      │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│      QueryResult                 │
├──────────────────────────────────┤
│ - matching_ids: string[]         │
│ - filter_parsed: {               │
│     attribute: string            │
│     operator: string             │
│     value: any                   │
│   }                              │
│ - message: string                │
└──────────────────────────────────┘
```

### Backend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Flask Application                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         server.py                                    │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Global State:                                                         │  │
│  │  - _buildings_cache: Building[]                                      │  │
│  │                                                                       │  │
│  │ Routes:                                                               │  │
│  │  + GET /api/buildings                                                │  │
│  │    └─> Returns: {data: Building[], error: string}                   │  │
│  │  + POST /api/query                                                   │  │
│  │    └─> Input: {query: string}                                       │  │
│  │    └─> Returns: {data: {matching_ids, filter_parsed}, error}       │  │
│  │  + HEAD / (health check)                                             │  │
│  │                                                                       │  │
│  │ Startup:                                                              │  │
│  │  + initialize_cache() -> void                                        │  │
│  │    └─> Calls get_all_buildings() and caches result                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│           │                           │                      │              │
│           ▼                           ▼                      ▼              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │  data_fetcher.py │    │llm_processor.py  │    │   CORS, JSON        │  │
│  ├──────────────────┤    ├──────────────────┤    │   Middleware        │  │
│  │ Functions:       │    │ Functions:       │    └─────────────────────┘  │
│  │                  │    │                  │                             │
│  │ + fetch_        │    │ + process_query()│                             │
│  │   building_    │    │   : dict          │                             │
│  │   footprints() │    │                  │                             │
│  │   : Building[] │    │ + parse_llm_     │                             │
│  │                │    │   response()     │                             │
│  │ + fetch_        │    │   : dict         │                             │
│  │   property_    │    │                  │                             │
│  │   assessments()│    │ + extract_filter │                             │
│  │   : Assessment[]    │   (response)     │                             │
│  │                │    │   : dict         │                             │
│  │ + buildings_   │    └──────────────────┘                             │
│  │   intersect()  │                                                      │
│  │   : bool       │                                                      │
│  │                │                                                      │
│  │ + buildings_   │                                                      │
│  │   match_by_    │                                                      │
│  │   proximity()  │                                                      │
│  │   : bool       │                                                      │
│  │                │                                                      │
│  │ + combine_     │                                                      │
│  │   building_   │                                                      │
│  │   data()       │                                                      │
│  │   : Building[] │                                                      │
│  │                │                                                      │
│  │ + get_all_     │                                                      │
│  │   buildings()  │                                                      │
│  │   : Building[] │                                                      │
│  └──────────────────┘                                                    │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │          External API Calls (via requests library)                │ │
│  ├─────────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────────────┐     ┌──────────────────────────────┐  │ │
│  │  │ Calgary Open Data API    │     │ Hugging Face Inference API  │  │ │
│  │  ├──────────────────────────┤     ├──────────────────────────────┤  │ │
│  │  │ GET cchr-krqg.json       │     │ POST v1/chat/completions    │  │ │
│  │  │ (Building Footprints)    │     │ (LLM Query Parsing)         │  │ │
│  │  │                          │     │                             │  │ │
│  │  │ Returns:                 │     │ Input: {model, messages}    │  │ │
│  │  │ - polygon: Polygon       │     │                             │  │ │
│  │  │ - rooftop_elev_z: float  │     │ Returns: {choices: [{      │  │ │
│  │  │ - grd_elev_min_z: float  │     │   message: {content}       │  │ │
│  │  │ - struct_id: string      │     │ }]}                         │  │ │
│  │  └──────────────────────────┘     └──────────────────────────────┘  │ │
│  │  ┌──────────────────────────┐                                       │ │
│  │  │ GET 4bsw-nn7w.json       │                                       │ │
│  │  │ (Property Assessment)    │                                       │ │
│  │  │                          │                                       │ │
│  │  │ Returns:                 │                                       │ │
│  │  │ - multipolygon:          │                                       │ │
│  │  │   MultiPolygon           │                                       │ │
│  │  │ - address: string        │                                       │ │
│  │  │ - assessed_value: int    │                                       │ │
│  │  │ - land_use_designation   │                                       │ │
│  │  │ - year_of_construction   │                                       │ │
│  │  └──────────────────────────┘                                       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. SEQUENCE DIAGRAM

### A. Initial Page Load

```
Frontend (User)    App.js           API Server       Data Fetcher       Calgary APIs
     │              │                   │                  │                 │
     │─ Open App ──>│                   │                  │                 │
     │              │                   │                  │                 │
     │              │─ useEffect() ────>│                  │                 │
     │              │                   │                  │                 │
     │              │                   │─ get_all_      │                 │
     │              │                   │  buildings() ─>│                 │
     │              │                   │                  │                 │
     │              │                   │                  │─ fetch cchr- ─>│
     │              │                   │                  │  krqg.json     │
     │              │                   │                  │<─ [21 records] │
     │              │                   │                  │                 │
     │              │                   │                  │─ fetch 4bsw- ─>│
     │              │                   │                  │  nn7w.json     │
     │              │                   │                  │<─ [415 records]│
     │              │                   │                  │                 │
     │              │                   │                  │─ Match via ───┐│
     │              │                   │                  │  proximity    ││
     │              │                   │                  │<──────────────┘│
     │              │                   │                  │                 │
     │              │                   │<─ 21 combined ─┤                 │
     │              │                   │  buildings    │                 │
     │              │<─ {data: [...]} ─┤                 │                 │
     │              │                   │                 │                 │
     │              │─ setState() ─────┐│                 │                 │
     │              │                  ││                 │                 │
     │<─ Render 3D ─┤<─────────────────┘│                 │                 │
     │  Buildings   │                   │                 │                 │
     │              │                   │                 │                 │
```

### B. User Query Flow

```
Frontend (User)    QueryPanel.js    App.js           API Server      LLM Processor      HuggingFace
     │                  │              │                  │                  │               │
     │─ Type Query ───>│               │                  │                  │               │
     │  "buildings     │               │                  │                  │               │
     │   over 100 ft"  │               │                  │                  │               │
     │                 │               │                  │                  │               │
     │                 │─ Submit ─────>│                  │                  │               │
     │                 │  {query}      │                  │                  │               │
     │                 │               │                  │                  │               │
     │                 │               │─ POST /api/ ───>│                  │               │
     │                 │               │  query          │                  │               │
     │                 │               │                  │                  │               │
     │                 │               │                  │─ process_ ─────>│               │
     │                 │               │                  │  query()         │               │
     │                 │               │                  │                  │               │
     │                 │               │                  │                  │─ POST v1/  ─>│
     │                 │               │                  │                  │  chat/      │
     │                 │               │                  │                  │  completions│
     │                 │               │                  │                  │               │
     │                 │               │                  │                  │<─ {"choices"│
     │                 │               │                  │                  │  :[{message:│
     │                 │               │                  │                  │  {content:  │
     │                 │               │                  │                  │  "JSON"}}]} │
     │                 │               │                  │                  │               │
     │                 │               │                  │<─ {"attribute"  │               │
     │                 │               │                  │   :"height",    │               │
     │                 │               │                  │   "operator":   │               │
     │                 │               │                  │   ">", "value": │               │
     │                 │               │                  │   100}          │               │
     │                 │               │                  │                 │               │
     │                 │               │<─ {matching_ids│                 │               │
     │                 │               │   :[...],      │                 │               │
     │                 │               │   filter_...}  │                 │               │
     │                 │               │                 │                 │               │
     │                 │               │─ setState() ───┐│                 │               │
     │                 │               │                ││                 │               │
     │<─ Highlight ───┤<──────────────┘│                 │                 │               │
     │  Buildings     │                 │                 │                 │               │
     │  (green)       │                 │                 │                 │               │
     │                │                 │                 │                 │               │
```

### C. Building Click / Details

```
Frontend (3D Scene)   ThreeViewer.js      App.js         Building Details Modal
      │                    │                 │                      │
      │─ Click Building ──>│                 │                      │
      │  (raycaster)       │                 │                      │
      │                    │─ selectedId ───>│                      │
      │                    │                 │                      │
      │                    │                 │─ setState() ────────┐│
      │                    │                 │                    ││
      │<─ Highlight ───────┤<────────────────┘                    ││
      │  (yellow)          │                 │                    ││
      │                    │                 │─ Render Details ──>│
      │                    │                 │  Popup             │
      │                    │                 │                    │
      │                    │                 │                    │
      │                    │                 │  Address:          │
      │                    │                 │  Height:           │
      │                    │                 │  Zoning:           │
      │                    │                 │  Value:            │
      │                    │                 │  Year Built:       │
      │                    │                 │                    │
      │                    │                 │<─ Close ───────────│
      │                    │                 │                    │
      │<─ Deselect ────────┤<────────────────┘                    │
      │                    │                 │                    │
```

---

## 3. STATE MANAGEMENT FLOW

```
┌─────────────────────────────────────────────────────────┐
│                    App Component                         │
│                    (State Hub)                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  buildings: Building[]                                  │
│    ├─> Rendered by ThreeViewer                         │
│    └─> Displayed in QueryPanel results                 │
│                                                          │
│  selectedBuildingId: string | null                     │
│    ├─> Highlight in ThreeViewer (yellow)              │
│    └─> Show details popup                              │
│                                                          │
│  highlightedBuildingIds: string[]                      │
│    ├─> From query results                              │
│    └─> Highlight in ThreeViewer (green)               │
│        Non-matched buildings dim                        │
│                                                          │
│  queryText: string                                      │
│    └─> Controlled input in QueryPanel                  │
│                                                          │
│  queryResults: QueryResult | null                      │
│    ├─> From /api/query POST                            │
│    └─> Contains matching_ids & parsed filter           │
│                                                          │
│  loading: boolean                                       │
│    └─> Show spinner during API calls                   │
│                                                          │
│  error: string | null                                  │
│    └─> Display error message to user                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. DATA FLOW DIAGRAM

```
                    ┌─────────────────────┐
                    │  Calgary Open Data  │
                    │  (2 Endpoints)      │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
        ┌────────▼────────┐       ┌──────────▼──────────┐
        │  21 Footprints  │       │ 415 Assessments    │
        │ (Footprint Data)│       │ (Property Data)    │
        └────────┬────────┘       └──────────┬──────────┘
                 │                           │
                 └─────────────┬─────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Match by Proximity  │
                    │  (Haversine Distance)│
                    │  21/21 successful    │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────────┐
                    │ 21 Combined Buildings  │
                    │ (Full Attributes)      │
                    └──────────┬──────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        ┌───────▼────────┐          ┌─────────▼──────────┐
        │  Backend Cache │          │  API Response      │
        │  (startup)     │          │  GET /api/buildings│
        └───────┬────────┘          └─────────┬──────────┘
                │                             │
                │                    ┌────────▼──────────┐
                │                    │  Frontend State   │
                │                    │  buildings[]      │
                │                    └────────┬──────────┘
                │                             │
                │              ┌──────────────┴─────────────┐
                │              │                            │
                │       ┌──────▼──────┐          ┌──────────▼──────┐
                │       │ ThreeViewer │          │  QueryPanel     │
                │       │ 3D Scene    │          │  (Display/UI)   │
                │       └─────────────┘          └────────┬────────┘
                │                                         │
                │                                ┌────────▼──────────┐
                │                                │  User Query       │
                │                                │  "buildings > ... │
                │                                └────────┬──────────┘
                │                                         │
                │                             ┌───────────▼────────┐
                │                             │  LLM Processing    │
                │                             │  Parse Query       │
                │                             └───────────┬────────┘
                │                                         │
                │                             ┌───────────▼────────┐
                │                             │  Filter Results    │
                │                             │  matching_ids[]    │
                │                             └───────────┬────────┘
                │                                         │
                └─────────────┬───────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Update State:     │
                    │  - highlighted[]   │
                    │  - loading = false │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Re-render 3D      │
                    │  - Green: matched  │
                    │  - Gray: others    │
                    └────────────────────┘
```

---

## 5. COMPONENT INTERACTION MATRIX

| From / To      | ThreeViewer | QueryPanel | DetailsModal | API Server |
|----------------|-------------|------------|--------------|------------|
| **App**        | sendProps   | sendProps  | sendProps    | fetch      |
| **ThreeViewer**| N/A         | emit click | (via App)    | N/A        |
| **QueryPanel** | (via App)   | N/A        | (via App)    | N/A        |
| **DetailsModal** | (via App) | (via App)  | N/A          | N/A        |
| **API Server** | N/A         | N/A        | N/A          | N/A        |

---

## 6. Error Handling Flow

```
┌────────────────────────────────────────────────────────┐
│         Error Handling Architecture                    │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend Errors:                                      │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Network Error / API Timeout                    │  │
│  │  └─> Display: "Unable to fetch buildings"     │  │
│  │                                                 │  │
│  │ LLM Query Parse Failure                        │  │
│  │  └─> Display: "Couldn't parse query"          │  │
│  │                                                 │  │
│  │ 3D Rendering Error                            │  │
│  │  └─> Display: "WebGL not supported"           │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Backend Errors:                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ API Response Error                             │  │
│  │  └─> Return: {data: null, error: "msg"}       │  │
│  │                                                 │  │
│  │ Data Fetch Timeout                            │  │
│  │  └─> Retry with 120s timeout                  │  │
│  │                                                 │  │
│  │ Geometry Matching Failed                       │  │
│  │  └─> Log & continue (graceful degradation)   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
```

---

## Summary

This architecture provides:
- ✅ **Separation of Concerns**: Frontend handles UI/UX, backend handles data/LLM
- ✅ **Scalability**: Modular components, reusable API
- ✅ **Real-time Responsiveness**: Cached data + asynchronous queries
- ✅ **Robust Matching**: Centroid proximity fallback for geometry issues
- ✅ **Error Resilience**: Graceful error handling at each layer

**Key Technologies:**
- React (component state management)
- Three.js (3D rendering)
- Flask (API server)
- Shapely & proximity matching (geometry operations)
- Hugging Face (LLM inference)
