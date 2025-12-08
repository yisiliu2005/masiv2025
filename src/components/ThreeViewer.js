import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import './ThreeViewer.css';

/**
 * Three.js 3D city dashboard viewer
 * Renders buildings as extruded geometries and handles interaction
 */
const ThreeViewer = ({ buildings, highlightedIds, selectedId, onBuildingClick }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const buildingMeshesRef = useRef({});
  const raycasterRef = useRef(new THREE.Raycaster());
  const mouseRef = useRef(new THREE.Vector2());

  // Color constants
  const COLOR_DEFAULT = 0x6699cc;
  const COLOR_HIGHLIGHTED = 0xffaa00;
  const COLOR_SELECTED = 0xff0000;
  const COLOR_DIMMED = 0x445566;

  // Calculate bounds for the scene
  const calculateBounds = (buildings) => {
    if (buildings.length === 0) {
      return { minLat: 0, maxLat: 0, minLon: 0, maxLon: 0, centerLat: 0, centerLon: 0 };
    }

    let minLat = Infinity, maxLat = -Infinity;
    let minLon = Infinity, maxLon = -Infinity;

    buildings.forEach((b) => {
      minLat = Math.min(minLat, b.latitude);
      maxLat = Math.max(maxLat, b.latitude);
      minLon = Math.min(minLon, b.longitude);
      maxLon = Math.max(maxLon, b.longitude);
    });

    const centerLat = (maxLat + minLat) / 2;
    const centerLon = (maxLon + minLon) / 2;

    return { minLat, maxLat, minLon, maxLon, centerLat, centerLon };
  };

  // Convert lat/lon to 3D position (centered and scaled)
  const latLonTo3D = (lat, lon, bounds) => {
    // Center coordinates
    const latCentered = lat - bounds.centerLat;
    const lonCentered = lon - bounds.centerLon;

    // Scale to scene units (approx meters)
    const scale = 111000; // meters per degree at this latitude
    const x = lonCentered * scale * 0.63; // 0.63 = cos(51°) for longitude correction
    const z = -latCentered * scale; // negate for north-up

    return new THREE.Vector3(x, 0, z);
  };

  // Create a building mesh
  const createBuildingMesh = (building, bounds) => {
    if (!building.footprint || building.footprint.length === 0) {
      return null;
    }

    try {
      // Footprint is GeoJSON polygon coordinates [longitude, latitude]
      const coordinates = building.footprint[0]; // First ring of polygon

      // Create shape from coordinates
      const shape = new THREE.Shape();

      coordinates.forEach((coord, i) => {
        const [lon, lat] = coord;
        const pos = latLonTo3D(lat, lon, bounds);

        if (i === 0) {
          shape.moveTo(pos.x, pos.z);
        } else {
          shape.lineTo(pos.x, pos.z);
        }
      });
      shape.closePath();

      // Create extruded geometry; extrude along Y after rotation
      const rawHeight = Math.max(building.height || 12, 10);
      const extrusionHeight = rawHeight * 0.6; // scale up vertical exaggeration
      const geometry = new THREE.ExtrudeGeometry(shape, {
        depth: extrusionHeight,
        bevelEnabled: false,
      });

      // Rotate so extrusion goes up the Y axis and lift to ground level
      geometry.rotateX(Math.PI / 2);
      geometry.translate(0, extrusionHeight / 2, 0);

      // Create material - UNIQUE for each building
      const material = new THREE.MeshPhongMaterial({
        color: COLOR_DEFAULT,
        emissive: 0x000000,
        side: THREE.DoubleSide,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.userData.buildingId = building.id;
      mesh.userData.building = building;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      
      return mesh;
    } catch (error) {
      console.error('Error creating building mesh:', error);
      return null;
    }
  };

  // Initialize Three.js scene
  const initScene = () => {
    if (!containerRef.current) return;

    // Clear any existing canvases first
    while (containerRef.current.firstChild) {
      containerRef.current.removeChild(containerRef.current.firstChild);
    }

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xcccccc);
    sceneRef.current = scene;

    // Camera setup
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 2000);
    camera.position.set(-5, 180, 100); 
    camera.lookAt(3, -300, -100); 
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: false,
      powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(120, 180, 80);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 1024;
    directionalLight.shadow.mapSize.height = 1024;
    scene.add(directionalLight);

    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(360, 360);
    const groundMaterial = new THREE.MeshLambertMaterial({ color: 0xbbbbbb });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);


    // Handle window resize
    const handleResize = () => {
      const newWidth = containerRef.current?.clientWidth || width;
      const newHeight = containerRef.current?.clientHeight || height;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    // Animation loop - always render to capture material updates
    let isAnimating = true;
    const animate = () => {
      if (!isAnimating) return;
      
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      isAnimating = false;
      window.removeEventListener('resize', handleResize);
      
      // Clean up Three.js resources
      if (renderer) {
        renderer.dispose();
        if (renderer.domElement && renderer.domElement.parentNode) {
          renderer.domElement.parentNode.removeChild(renderer.domElement);
        }
      }
    };
  };

  // Initialize on mount
  useEffect(() => {
    const cleanup = initScene();
    return cleanup;
  }, []);

  // Rebuild meshes when buildings data changes
  useEffect(() => {
    if (!sceneRef.current || buildings.length === 0) return;

    // Remove old meshes
    Object.values(buildingMeshesRef.current).forEach((mesh) => {
      sceneRef.current.remove(mesh);
      mesh.geometry.dispose();
      if (Array.isArray(mesh.material)) {
        mesh.material.forEach((m) => m.dispose());
      } else {
        mesh.material.dispose();
      }
    });
    buildingMeshesRef.current = {};

    const bounds = calculateBounds(buildings);

    buildings.forEach((building) => {
      const mesh = createBuildingMesh(building, bounds);
      if (mesh) {
        sceneRef.current.add(mesh);
        buildingMeshesRef.current[building.id] = mesh;
      }
    });
  }, [buildings]);

  // Update building colors based on highlights
  useEffect(() => {
    Object.entries(buildingMeshesRef.current).forEach(([buildingId, mesh]) => {
      let color = COLOR_DEFAULT;

      if (selectedId === buildingId) {
        color = COLOR_SELECTED;
      } else if (highlightedIds && highlightedIds.includes(buildingId)) {
        color = COLOR_HIGHLIGHTED;
      } else if (highlightedIds && highlightedIds.length > 0) {
        color = COLOR_DIMMED; // Dim non-matching buildings
      }

      // Update the color
      mesh.material.color.setHex(color);
    });
  }, [highlightedIds, selectedId]);

  // Handle clicks on buildings
  useEffect(() => {
    const handleWindowClick = (event) => {
      // Only process canvas clicks
      if (event.target.tagName !== 'CANVAS') {
        return;
      }

      const rect = event.target.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);

      const intersects = raycasterRef.current.intersectObjects(
        Object.values(buildingMeshesRef.current)
      );

      if (intersects.length > 0) {
        const building = intersects[0].object.userData.building;
        onBuildingClick(building);
      }
    };

    window.addEventListener('click', handleWindowClick, false);
    return () => window.removeEventListener('click', handleWindowClick, false);
  }, [onBuildingClick]);

  return <div ref={containerRef} className="three-viewer" />;
};

export default ThreeViewer;
