import React, { useState, useEffect } from 'react'
// soda-js kept if needed later; not used in runtime
import * as soda from 'soda-js'
import * as THREE from 'three'
import './App.css'
import ThreeViewer from './components/ThreeViewer'
import QueryPanel from './components/QueryPanel'
import { fetchBuildings } from './services/api'

/* render within this rectangle:
  top left: 51.03999458794443, -114.07919451901128
  top right: 51.03982364829675, -114.07429304853973
  bottom left: 51.03902424569097, -114.07927447774654
  bottom right: 51.03893877415592, -114.074373007275
*/

function App() {
  const [buildings, setBuildings] = useState([])
  const [highlightedIds, setHighlightedIds] = useState([])
  const [selectedBuilding, setSelectedBuilding] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch buildings on component mount
  useEffect(() => {
    const loadBuildings = async () => {
      setLoading(true)
      const data = await fetchBuildings()
      if (data.length > 0) {
        setBuildings(data)
        setError(null)
      } else {
        setError('Failed to load buildings')
      }
      setLoading(false)
    }

    loadBuildings()
  }, [])

  const handleQueryResult = (matchingIds) => {
    setHighlightedIds(matchingIds)
  }

  const handleBuildingClick = (building) => {
    setSelectedBuilding(building)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Calgary 3D City Dashboard</h1>
        <p>Explore buildings and query with natural language</p>
      </header>

      <div className="app-main">
        <div className="viewer-container">
          {loading ? (
            <div className="loading">Loading buildings...</div>
          ) : error ? (
            <div className="error">Error: {error}</div>
          ) : (
            <ThreeViewer 
              buildings={buildings} 
              highlightedIds={highlightedIds}
              selectedId={selectedBuilding?.id}
              onBuildingClick={handleBuildingClick}
            />
          )}
        </div>

        <div className="sidebar">
          <QueryPanel 
            onQueryResult={handleQueryResult}
            buildings={buildings}
          />

          {selectedBuilding && (
            <div className="building-details">
              <h3>Building Details</h3>
              <div className="detail-item">
                <strong>Address:</strong> {selectedBuilding.address || 'N/A'}
              </div>
              <div className="detail-item">
                <strong>Height:</strong> {selectedBuilding.height?.toFixed(1)} meters
              </div>
              <div className="detail-item">
                <strong>Zoning:</strong> {selectedBuilding.land_use_designation || 'N/A'}
              </div>
              <div className="detail-item">
                <strong>Assessed Value:</strong> ${selectedBuilding.assessed_value?.toLocaleString()}
              </div>
              <div className="detail-item">
                <strong>Year Built:</strong> {selectedBuilding.year_of_construction || 'N/A'}
              </div>
              <button 
                onClick={() => setSelectedBuilding(null)}
                className="close-details-button"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
