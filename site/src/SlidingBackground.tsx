import React from 'react';

interface SlidingBackgroundProps {
  cartPosition: number;
  width: number;
  height: number;
  positionRange?: { min: number; max: number };
}

const SlidingBackground: React.FC<SlidingBackgroundProps> = ({
  cartPosition,
  width,
  height,
  positionRange
}) => {
  // World boundaries - use provided range or defaults
  const minTrack = positionRange?.min ?? -20; // minimum x position in meters
  const maxTrack = positionRange?.max ?? 20;  // maximum x position in meters

  // Scale and positioning
  const scale = 100; // pixels per meter
  const centerX = width / 2;
  const centerY = height * 0.65;
  
  // Ground and track positioning
  const groundY = centerY + 40;
  const trackY = groundY - 5;
  
  // Calculate background offset to keep cart centered
  const backgroundOffset = -cartPosition * scale;

  // Generate complete background for entire track range
  const generateWorldBackground = () => {
    const elements = [];
    
    // Generate track for entire range
    for (let worldX = minTrack; worldX <= maxTrack; worldX += 1) { // Every 1 meter
      const screenX = centerX + (worldX * scale) + backgroundOffset;
      
      // Skip if not visible
      if (screenX < -100 || screenX > width + 100) continue;
      
      // Track segment
      elements.push(
        <rect 
          key={`track-${worldX}`}
          x={screenX - 50} 
          y={trackY+5} 
          width="100" 
          height="10"
          fill="#696969"
        />
      );
      
      // Railroad ties every 1 meter
      if ((worldX - minTrack) % 2 === 0) {
        elements.push(
          <rect 
            key={`tie-${worldX}`}
            x={screenX} 
            y={trackY+5} 
            width="50" 
            height="10"
            fill="#4a4a4aff"
          />
        );
      }
    }
    
    // Generate background scenery every 3 meters (more objects)
    for (let worldX = Math.ceil(minTrack / 3) * 3; worldX <= maxTrack; worldX += 2) {
      const screenX = centerX + (worldX * scale) + backgroundOffset;
      
      // Skip if not visible or if it's a 5m marker position
      if (screenX < -200 || screenX > width + 200 || worldX % 5 === 0) continue;
      
      // Use position as seed for consistent random generation
      const seed = worldX / 3;
      const random1 = Math.sin(seed * 12.9898) * 43758.5453;
      const random2 = Math.sin(seed * 78.233) * 43758.5453;
      const r1 = (random1 - Math.floor(random1));
      const r2 = (random2 - Math.floor(random2));
      
      if (r1 < 0.25) {
        // Trees with properly proportioned trunks
        const treeHeight = 20 + r2 * 60;
        const foliageRadius = 20 + r2 * 8; // Scale foliage with height
        const trunkWidth = Math.max(6, foliageRadius * 0.3); // Trunk width proportional to foliage
        const trunkHeight = treeHeight; // Trunk is 60% of tree height
        elements.push(
          <g key={`tree-${worldX}`}>
            <rect 
              x={screenX - trunkWidth/2} 
              y={groundY - trunkHeight} 
              width={trunkWidth} 
              height={trunkHeight} 
              fill="#8B4513" 
            />
            <circle cx={screenX} cy={groundY - trunkHeight + foliageRadius/2} r={foliageRadius} fill="#228B22" />
            <circle cx={screenX - foliageRadius*0.4} cy={groundY - trunkHeight + foliageRadius*0.7} r={foliageRadius*0.7} fill="#32CD32" />
            <circle cx={screenX + foliageRadius*0.5} cy={groundY - trunkHeight + foliageRadius*0.8} r={foliageRadius*0.8} fill="#228B22" />
          </g>
        );
      } else if (r1 < 0.45) {
        // Buildings
        const buildingHeight = 80 + r2 * 60;
        const buildingWidth = 50;
        const buildingY = groundY - buildingHeight;
        elements.push(
          <g key={`building-${worldX}`}>
            <rect 
              x={screenX - buildingWidth/2} 
              y={buildingY} 
              width={buildingWidth} 
              height={buildingHeight} 
              fill="#708090" 
              stroke="#2F4F4F" 
              strokeWidth="1"
            />
            {/* Windows */}
            {Array.from({length: Math.floor(r2 * 4) + 2}).map((_, i) => (
              <rect 
                key={i}
                x={screenX - buildingWidth/2 + 10} 
                y={buildingY + 15 + i * 20} 
                width="8" 
                height="12" 
                fill="#FFD700" 
              />
            ))}
          </g>
        );
      } else if (r1 < 0.6) {
        // Bushes/shrubs
        const bushSize = 15 + r2 * 10;
        elements.push(
          <g key={`bush-${worldX}`}>
            <circle cx={screenX - 8} cy={groundY - bushSize/2} r={bushSize/2} fill="#90EE90" />
            <circle cx={screenX + 5} cy={groundY - bushSize/2 + 3} r={bushSize/2 - 2} fill="#228B22" />
            <circle cx={screenX} cy={groundY - bushSize/2 - 2} r={bushSize/2 - 1} fill="#32CD32" />
          </g>
        );
      } else if (r1 < 0.75) {
        // Lamp posts
        const lampHeight = 45 + r2 * 15;
        elements.push(
          <g key={`lamp-${worldX}`}>
            <rect x={screenX - 2} y={groundY - lampHeight} width="4" height={lampHeight} fill="#2F4F4F" />
            <circle cx={screenX} cy={groundY - lampHeight} r="8" fill="#FFE4B5" stroke="#FFA500" strokeWidth="2" />
            <circle cx={screenX} cy={groundY - lampHeight} r="5" fill="#FFFF99" />
          </g>
        );
      } else if (r1 < 0.85) {
        // Benches
        elements.push(
          <g key={`bench-${worldX}`}>
            <rect x={screenX - 15} y={groundY - 8} width="30" height="3" fill="#8B4513" />
            <rect x={screenX - 15} y={groundY - 20} width="30" height="3" fill="#8B4513" />
            <rect x={screenX - 12} y={groundY - 20} width="2" height="12" fill="#696969" />
            <rect x={screenX + 10} y={groundY - 20} width="2" height="12" fill="#696969" />
          </g>
        );
      } else {
        // Power/phone poles
        const poleHeight = 70 + r2 * 30;
        elements.push(
          <g key={`pole-${worldX}`}>
            <rect x={screenX - 3} y={groundY - poleHeight} width="6" height={poleHeight} fill="#8B4513" />
            <line x1={screenX - 20} y1={groundY - poleHeight + 20} x2={screenX + 20} y2={groundY - poleHeight + 20} 
                  stroke="#2F4F4F" strokeWidth="2" />
            <line x1={screenX - 20} y1={groundY - poleHeight + 30} x2={screenX + 20} y2={groundY - poleHeight + 30} 
                  stroke="#2F4F4F" strokeWidth="2" />
          </g>
        );
      }
    }
    
    // Generate clouds (independent of ground features)
    for (let worldX = minTrack; worldX <= maxTrack; worldX += 12) {
      const screenX = centerX + (worldX * scale) + backgroundOffset;
      
      // Skip if not visible
      if (screenX < -100 || screenX > width + 100) continue;
      
      const seed = worldX / 12;
      const random1 = Math.sin(seed * 15.789) * 43758.5453;
      const random2 = Math.sin(seed * 91.234) * 43758.5453;
      const r1 = (random1 - Math.floor(random1));
      const r2 = (random2 - Math.floor(random2));
      
      if (r1 < 0.4) {
        const cloudY = 30 + r2 * 40;
        const cloudSize = 12 + r2 * 8;
        elements.push(
          <g key={`cloud-${worldX}`}>
            <circle cx={screenX - 15} cy={cloudY} r={cloudSize} fill="rgba(255,255,255,0.8)" />
            <circle cx={screenX} cy={cloudY} r={cloudSize + 4} fill="rgba(255,255,255,0.8)" />
            <circle cx={screenX + 15} cy={cloudY} r={cloudSize} fill="rgba(255,255,255,0.8)" />
          </g>
        );
      }
    }
    
    // Generate meter markers every 5 meters (RENDERED LAST - in front of everything)
    for (let worldX = Math.ceil(minTrack / 5) * 5; worldX <= maxTrack; worldX += 5) {
      const screenX = centerX + (worldX * scale) + backgroundOffset;
      
      // Skip if not visible
      if (screenX < -100 || screenX > width + 100) continue;
      
      // Distance marker with proper sign board
      elements.push(
        <g key={`marker-${worldX}`}>
          {/* Pole */}
          <rect 
            x={screenX - 4} 
            y={groundY - 70} 
            width="8" 
            height="70"
            fill="#FFD700"
            stroke="#FFA500"
            strokeWidth="2"
          />
          {/* Sign board */}
          <rect 
            x={screenX - 25} 
            y={groundY - 85} 
            width="50" 
            height="20"
            fill="#FFFFFF"
            stroke="#2F4F4F"
            strokeWidth="2"
            rx="3"
          />
          {/* Text */}
          <text 
            x={screenX} 
            y={groundY - 70} 
            fontSize="16" 
            fill="#2F4F4F"
            fontFamily="Arial, sans-serif"
            textAnchor="middle"
            fontWeight="bold"
          >
            {worldX}m
          </text>
        </g>
      );
    }
    
    return elements;
  };

  return <>{generateWorldBackground()}</>;
};

export default SlidingBackground;