import React, {useState, useEffect} from 'react'
import * as soda from 'soda-js'
import * as THREE from 'three'

// Get and store building footprint and height data for rendering:
var building = new soda.Consumer('https://data.calgary.ca/resource/cchr-krqg.json');
//building.query()

//get other building data such as property assessment from backend

function App() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/members')
      .then(response => response.json())
      .then(data => setData(data));
  }, []);
  return (
    <div>
      text
    </div>
  )
}

export default App
