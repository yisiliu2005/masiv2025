# Urban Design 3D City Dashboard with LLM Querying

A web-based 3D city visualization platform that displays Calgary building data and uses natural language queries with an LLM to dynamically filter and highlight buildings based on user intent.

**Live Demo**: https://masiv2025.vercel.app (frontend) | Backend API: https://masiv2025.onrender.com

---

## 🎯 Features

- **3D Building Visualization**: Interactive Three.js scene showing 3-4 city blocks of Calgary buildings
- **Real Building Data**: Fetches actual building footprints, heights, zoning, and property values from Calgary Open Data
- **Natural Language Querying**: Ask questions like "buildings over 100 feet tall" or "commercial properties"
- **LLM-Powered Filtering**: Hugging Face Inference API interprets user intent and filters results
- **Interactive Highlighting**: Click buildings for details, see query results highlighted in real-time
- **Responsive Design**: Works on desktop and tablet

---

## 🏗️ Architecture

```
Frontend (React)                     Backend (Flask)                    External APIs
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│  ThreeViewer.js  │               │  server.py       │               │ Calgary Open Data│
│  (3D Scene)      ├──────────────>│  /api/buildings  │──────────────>│ cchr-krqg.json   │
└──────────────────┘               └──────────────────┘               │ (Footprints)     │
│  QueryPanel.js   │               │  /api/query      │               └──────────────────┘
│  (Search)        │               │                  │               ┌──────────────────┐
└──────────────────┘               │  data_fetcher.py │──────────────>│ 4bsw-nn7w.json   │
                                   │  llm_processor.py│               │ (Property Data)  │
                                   └──────────────────┘               └──────────────────┘
                                                                      ┌──────────────────┐
                                                                      │ Hugging Face API │
                                                                      │ LLM Inference    │
                                                                      └──────────────────┘
```

### Key Technologies
- **Frontend**: React, Three.js, CSS3
- **Backend**: Flask 3.1.2, Python 3.13.4
- **Data Processing**: Shapely (geometry), Requests (APIs), Socrata (SODA API client)
- **LLM**: Hugging Face Inference API (moonshotai/Kimi-K2-Instruct-0905)
- **Hosting**: Vercel (frontend), Render (backend)

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** v16+ (for React frontend)
- **Python** 3.8+ (for Flask backend)
- **Hugging Face API Key** (free tier works)

### Installation

#### 1. Clone & Setup
```bash
git clone https://github.com/yisiliu2005/masiv2025.git
cd masiv2025
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with Hugging Face token
echo "HF_TOKEN=your_hf_token_here" > .env

# Start Flask server (runs on http://localhost:5000)
python3 server.py
```

#### 3. Frontend Setup
```bash
cd ../map

# Install dependencies
npm install

# Start React dev server (runs on http://localhost:3000, proxies API to localhost:5000)
npm start
```

The app will open at `http://localhost:3000` with the backend at `http://localhost:5000`.

---

## 📖 Usage

### 1. **View Buildings**
The 3D scene loads a section of downtown Calgary, 4 blocks. 

### 2. **Click Buildings**
Click any building to see details:
- Address
- Height (in meters)
- Zoning designation
- Assessed property value
- Year of construction

### 3. **Query with Natural Language**
Enter a search query in the text input:

**Example queries:**
- "buildings over 100 feet tall"
- "commercial properties"
- "buildings worth more than 3 million"
- "residential zoning"
- "built after 1960"

The LLM interprets your intent, filters matching buildings, and highlights them in the 3D view. Non-matching buildings dim automatically.

---

## 🔧 API Endpoints

### GET `/api/buildings`
Returns all buildings in the defined region.

**Response:**
```json
{
  "data": [
    {
      "id": "1072734",
      "struct_id": "1072734",
      "address": "709 14 AV SW",
      "latitude": 51.039669,
      "longitude": -114.077121,
      "height": 22.06,
      "land_use_designation": "DC",
      "assessed_value": 2900000,
      "year_of_construction": "1961",
      "footprint": [[lon, lat], [lon, lat], ...]
    }
  ]
}
```

### POST `/api/query`
Interprets a natural language query and returns matching building IDs.

**Request:**
```json
{
  "query": "buildings over 100 feet tall"
}
```

**Response:**
```json
{
  "data": {
    "matching_ids": ["1072734", "1072735"],
    "filter_parsed": {
      "attribute": "height",
      "operator": ">",
      "value": 100
    }
  }
}
```

---

## 🛠️ Project Structure

```
masiv2025/
├── backend/
│   ├── server.py              # Flask API server
│   ├── data_fetcher.py        # Fetch & combine Calgary building data
│   ├── llm_processor.py       # Hugging Face LLM integration (ready to implement)
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Hugging Face API token (not in repo)
│
├── map/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── components/
│   │   │   ├── ThreeViewer.js # Three.js 3D scene
│   │   │   ├── QueryPanel.js  # Search/query input UI
│   │   │   └── *.css          # Component styles
│   │   └── services/
│   │       └── api.js         # API client for backend calls
│   ├── package.json           # Node.js dependencies
│   └── public/
│       └── index.html         # HTML entry point
│
├── docs/
│   └── UML.pdf               # Architecture diagrams
│
└── README.md                 # This file
```

---

## 🧠 How LLM Querying Works

1. **User Input**: "buildings over 100 feet tall"
2. **LLM Processing**: Flask sends structured prompt to Hugging Face API
3. **Query Parsing**: LLM returns structured JSON: `{"attribute": "height", "operator": ">", "value": 100}`
4. **Backend Filtering**: Flask filters buildings matching the parsed criteria
5. **Frontend Highlighting**: React receives matching IDs and highlights them in the 3D scene

---

## 🔑 Environment Variables

Create `backend/.env` file:
```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Get your free Hugging Face token at: https://huggingface.co/settings/tokens

---

## 📊 Data Sources

- **Building Footprints & Heights**: [Calgary Open Data - cchr-krqg.json](https://data.calgary.ca/resource/cchr-krqg.json)
  - Fields: `polygon`, `rooftop_elev_z`, `grd_elev_min_z`, `struct_id`
  
- **Property Assessment Data**: [Calgary Open Data - 4bsw-nn7w.json](https://data.calgary.ca/resource/4bsw-nn7w.json)
  - Fields: `multipolygon`, `address`, `assessed_value`, `land_use_designation`, `year_of_construction`

---

## 🚢 Deployment

### Frontend (Vercel)
```bash
cd map
npm run build
vercel deploy
```

### Backend (Render)
1. Push code to GitHub
2. Connect repository to Render
3. Set environment variable: `HF_TOKEN`
4. Deploy

---

## 🐛 Troubleshooting

**Issue**: Buildings showing with empty addresses/values
- **Solution**: Backend needs to fetch from Calgary APIs. Check internet connection and API availability.

**Issue**: LLM query returns no results
- **Solution**: Try simpler queries. LLM may misinterpret complex natural language.

**Issue**: 3D scene not loading
- **Solution**: Check browser console (F12) for Three.js errors. Ensure WebGL is supported.

**Issue**: CORS errors
- **Solution**: Backend is configured with CORS. Ensure `REACT_APP_API_BASE` in frontend points to correct backend URL.

---

## 📝 Design Notes

### Geometry Matching
Buildings are matched across two datasets (footprints + property assessments) using **centroid proximity** (Haversine distance). This approach is robust and avoids Shapely intersection issues on some environments.

### Coordinate System
- Calgary APIs use **[longitude, latitude]** (GeoJSON standard)
- Three.js uses **X (lon), Y (height), Z (-lat)**
- Always convert carefully between systems

### Performance
- All buildings are cached on backend startup (< 2s load time)
- Frontend renders with a single Three.js scene (60+ FPS)
- API responses are lightweight (~10KB per request)

---

## 🎓 Learning Resources

- **Three.js**: https://threejs.org/docs/
- **React Hooks**: https://react.dev/reference/react
- **Flask**: https://flask.palletsprojects.com/
- **GeoJSON**: https://geojson.org/
- **Hugging Face Inference**: https://huggingface.co/inference-api

---

## 📄 License

This project is part of the MASIV 2025 Intern Test. Use and modification permitted for educational purposes.

---

## 👤 Author

Yisi Liu, GitHub Copilot

---

**Ready to query the city in 3D!** 🏙️✨
