import React, { useEffect, useState } from 'react';

interface CartPoleProps {
  cartPosition: number; // x position of the cart
  poleAngle: number;    // angle of the pole in radians
  forces?: number[];    // forces array [cart_force, pole_torque]
  width?: number;       // canvas width
  height?: number;      // canvas height
  smoothTransition?: boolean; // enable smooth transitions
  positionRange?: { min: number; max: number };
  forceRange?: { min: number; max: number };
}

const CartPole: React.FC<CartPoleProps> = ({ 
  cartPosition, 
  poleAngle, 
  forces = [0, 0],
  width = 800, 
  height = 400,
  smoothTransition = true,
  positionRange,
  forceRange
}) => {
  // Internal state for smooth interpolation
  const [displayCartPosition, setDisplayCartPosition] = useState(cartPosition);
  const [displayPoleAngle, setDisplayPoleAngle] = useState(poleAngle);
  const [displayForces, setDisplayForces] = useState(forces);

  // Responsive dimensions based on screen size
  const getResponsiveDimensions = () => {
    if (typeof window === 'undefined') return { width, height };
    
    const screenWidth = window.innerWidth;
    
    if (screenWidth < 480) {
      // Mobile - tall rectangular aspect ratio (1:3)
      return { width: 300, height: 425 };
    } else if (screenWidth < 768) {
      // Tablet - tall rectangular aspect ratio (1:2)
      return { width: 300, height: 300 };
    } else {
      // Desktop - wider aspect ratio (2:1)
      return { width: 700, height: 300 };
    }
  };

  const [dimensions, setDimensions] = useState(getResponsiveDimensions);

  // Update dimensions on window resize
  useEffect(() => {
    const handleResize = () => {
      setDimensions(getResponsiveDimensions());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const responsiveWidth = dimensions.width;
  const responsiveHeight = dimensions.height;

  // World boundaries - use provided range or defaults
  const minTrack = positionRange?.min ?? -20; // minimum x position in meters
  const maxTrack = positionRange?.max ?? 20;  // maximum x position in meters

  // Force scaling - use provided range or defaults
  const minForce = forceRange?.min ?? -20; // minimum force/torque
  const maxForce = forceRange?.max ?? 20;  // maximum force/torque
  const maxForceRange = Math.max(Math.abs(minForce), Math.abs(maxForce));

  // Smooth interpolation effect
  useEffect(() => {
    if (!smoothTransition) {
      setDisplayCartPosition(cartPosition);
      setDisplayPoleAngle(poleAngle);
      setDisplayForces(forces);
      return;
    }

    const startCart = displayCartPosition;
    const startPole = displayPoleAngle;
    const startForces = displayForces;
    const targetCart = cartPosition;
    const targetPole = poleAngle;
    const targetForces = forces;
    
    const startTime = performance.now();
    const duration = 100;
    
    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeOut = 1 - Math.pow(1 - progress, 2.5);
      
      const newCartPos = startCart + (targetCart - startCart) * easeOut;
      const newPoleAngle = startPole + (targetPole - startPole) * easeOut;
      const newForces = [
        startForces[0] + (targetForces[0] - startForces[0]) * easeOut,
        startForces[1] + (targetForces[1] - startForces[1]) * easeOut
      ];
      
      setDisplayCartPosition(newCartPos);
      setDisplayPoleAngle(newPoleAngle);
      setDisplayForces(newForces);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [cartPosition, poleAngle, forces, smoothTransition]);

  // Scale and positioning
  const scale = 100; // pixels per meter
  const centerX = responsiveWidth / 2;
  const centerY = responsiveHeight * 0.65;
  
  // Ground and track positioning
  const groundY = centerY + 40;
  const trackY = groundY - 5;
  
  // Calculate background offset to keep cart centered
  const backgroundOffset = -displayCartPosition * scale;
  
  // Cart properties - always centered on screen
  const cartWidth = 60;
  const cartHeight = 30;
  const cartX = centerX - cartWidth / 2;
  const cartY = trackY - cartHeight;
  
  // Pole properties
  const poleLength = 80;
  const poleWidth = 6;
  const poleEndX = cartX + cartWidth / 2 + Math.sin(displayPoleAngle) * poleLength;
  const poleEndY = cartY - Math.cos(displayPoleAngle) * poleLength;
  
  // Wheel properties
  const wheelRadius = 12;
  const wheel1X = cartX + 15;
  const wheel2X = cartX + cartWidth - 15;
  const wheelY = cartY + cartHeight;
  
  // Calculate wheel rotation based on cart position
  const wheelRotation = (displayCartPosition / (wheelRadius * 2 * Math.PI / scale)) * 360;
  
  // Generate complete background for entire track range
  const generateWorldBackground = () => {
    const elements = [];
    
    // Generate track for entire range
    for (let worldX = minTrack; worldX <= maxTrack; worldX += 1) { // Every 1 meter
      const screenX = centerX + (worldX * scale) + backgroundOffset;
      
      // Skip if not visible
      if (screenX < -100 || screenX > responsiveWidth + 100) continue;
      
      // Track segment
      elements.push(
        <rect 
          key={`track-${worldX}`}
          x={screenX - 50} 
          y={trackY} 
          width="100" 
          height="10"
          fill="#696969"
        />
      );
      
      // Railroad ties every 0.5 meters
      if (worldX % 0.5 === 0) {
        elements.push(
          <rect 
            key={`tie-${worldX}`}
            x={screenX - 30} 
            y={trackY - 2} 
            width="60" 
            height="14"
            fill="#8B4513"
          />
        );
      }
    }
    
    // Generate background scenery every 3 meters (more objects)
    for (let worldX = Math.ceil(minTrack / 3) * 3; worldX <= maxTrack; worldX += 3) {
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
        const treeHeight = 60 + r2 * 40;
        const foliageRadius = 20 + r2 * 8; // Scale foliage with height
        const trunkWidth = Math.max(6, foliageRadius * 0.3); // Trunk width proportional to foliage
        const trunkHeight = treeHeight * 0.6; // Trunk is 60% of tree height
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
      if (screenX < -100 || screenX > responsiveWidth + 100) continue;
      
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
      if (screenX < -100 || screenX > responsiveWidth + 100) continue;
      
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

  return (
    <div className="flex flex-col items-center w-full max-w-full">
      <h3 className="text-lg font-semibold mb-2">Cart Pole Visualization</h3>
      <div className="w-full max-w-4xl overflow-hidden">
        <svg 
          viewBox={`0 0 ${responsiveWidth} ${responsiveHeight}`}
          className="w-full h-auto border border-gray-300 bg-gradient-to-b from-sky-200 to-sky-50"
          preserveAspectRatio="xMidYMid meet"
        >
        {/* Background elements that scroll with cart position */}
        {generateWorldBackground()}
        
        {/* Ground line */}
        <line 
          x1={0} 
          y1={groundY} 
          x2={responsiveWidth} 
          y2={groundY}
          stroke="#8B5A3C" 
          strokeWidth="3"
        />        {/* Cart shadow */}
        <ellipse 
          cx={cartX + cartWidth / 2 + 3} 
          cy={wheelY + wheelRadius + 8} 
          rx={cartWidth / 2 + 5} 
          ry="8"
          fill="rgba(0,0,0,0.2)"
        />
        
        {/* Cart body */}
        <rect 
          x={cartX} 
          y={cartY} 
          width={cartWidth} 
          height={cartHeight}
          fill="#FF6B6B"
          stroke="#E55454"
          strokeWidth="2"
          rx="5"
        />
        
        {/* Cart details */}
        <rect 
          x={cartX + 5} 
          y={cartY + 5} 
          width={cartWidth - 10} 
          height={cartHeight - 10}
          fill="#FF8E8E"
          rx="3"
        />
        
        {/* Wheels with rotation */}
        <g>
          {/* Wheel 1 */}
          <circle 
            cx={wheel1X} 
            cy={wheelY} 
            r={wheelRadius}
            fill="#4A4A4A"
            stroke="#2A2A2A"
            strokeWidth="2"
          />
          <g transform={`rotate(${wheelRotation} ${wheel1X} ${wheelY})`}>
            <line x1={wheel1X - 6} y1={wheelY} x2={wheel1X + 6} y2={wheelY} stroke="#2A2A2A" strokeWidth="2" />
            <line x1={wheel1X} y1={wheelY - 6} x2={wheel1X} y2={wheelY + 6} stroke="#2A2A2A" strokeWidth="2" />
            <line x1={wheel1X - 4} y1={wheelY - 4} x2={wheel1X + 4} y2={wheelY + 4} stroke="#2A2A2A" strokeWidth="1" />
            <line x1={wheel1X - 4} y1={wheelY + 4} x2={wheel1X + 4} y2={wheelY - 4} stroke="#2A2A2A" strokeWidth="1" />
          </g>
          
          {/* Wheel 2 */}
          <circle 
            cx={wheel2X} 
            cy={wheelY} 
            r={wheelRadius}
            fill="#4A4A4A"
            stroke="#2A2A2A"
            strokeWidth="2"
          />
          <g transform={`rotate(${wheelRotation} ${wheel2X} ${wheelY})`}>
            <line x1={wheel2X - 6} y1={wheelY} x2={wheel2X + 6} y2={wheelY} stroke="#2A2A2A" strokeWidth="2" />
            <line x1={wheel2X} y1={wheelY - 6} x2={wheel2X} y2={wheelY + 6} stroke="#2A2A2A" strokeWidth="2" />
            <line x1={wheel2X - 4} y1={wheelY - 4} x2={wheel2X + 4} y2={wheelY + 4} stroke="#2A2A2A" strokeWidth="1" />
            <line x1={wheel2X - 4} y1={wheelY + 4} x2={wheel2X + 4} y2={wheelY - 4} stroke="#2A2A2A" strokeWidth="1" />
          </g>
        </g>
        
        {/* Pole */}
        <line 
          x1={cartX + cartWidth / 2} 
          y1={cartY} 
          x2={poleEndX} 
          y2={poleEndY}
          stroke="#8B4513"
          strokeWidth={poleWidth}
          strokeLinecap="round"
        />
        
        {/* Pole highlight */}
        <line 
          x1={cartX + cartWidth / 2} 
          y1={cartY} 
          x2={poleEndX} 
          y2={poleEndY}
          stroke="#CD853F"
          strokeWidth={poleWidth - 2}
          strokeLinecap="round"
        />
        
        {/* Pole tip (mass) */}
        <circle 
          cx={poleEndX} 
          cy={poleEndY} 
          r="8"
          fill="#FFD700"
          stroke="#FFA500"
          strokeWidth="2"
        />
        
        {/* Pole tip highlight */}
        <circle 
          cx={poleEndX - 2} 
          cy={poleEndY - 2} 
          r="3"
          fill="#FFFF99"
        />
        
        {/* Pivot point */}
        <circle 
          cx={cartX + cartWidth / 2} 
          cy={cartY} 
          r="4"
          fill="#2A2A2A"
        />
        
        {/* Force visualization */}
        {displayForces && (displayForces[0] !== 0 || displayForces[1] !== 0) && (
          <g>
            {/* Cart force arrow (horizontal) */}
            {displayForces[0] !== 0 && (
              <g>
                {/* Force arrow for cart */}
                <defs>
                  <marker id="arrowhead-cart" markerWidth="10" markerHeight="7" 
                          refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#FF4500" />
                  </marker>
                </defs>
                <line 
                  x1={cartX + cartWidth / 2} 
                  y1={cartY + cartHeight / 2} 
                  x2={cartX + cartWidth / 2 + Math.sign(displayForces[0]) * Math.min((Math.abs(displayForces[0]) / maxForceRange) * 80, 80)} 
                  y2={cartY + cartHeight / 2}
                  stroke="#FF4500" 
                  strokeWidth="4"
                  markerEnd="url(#arrowhead-cart)"
                />
                {/* Force label */}
                <text 
                  x={cartX + cartWidth / 2 + Math.sign(displayForces[0]) * (Math.min((Math.abs(displayForces[0]) / maxForceRange) * 80, 80) / 2)} 
                  y={cartY + cartHeight / 2 - 10} 
                  fontSize="10" 
                  fill="#FF4500"
                  fontFamily="Arial, sans-serif"
                  textAnchor="middle"
                  fontWeight="bold"
                >
                  F={displayForces[0].toFixed(1)}N
                </text>
              </g>
            )}
            
            {/* Pole torque arc arrow */}
            {displayForces[1] !== 0 && (
              <g>
                <defs>
                  <marker id="arrowhead-torque" markerWidth="6" markerHeight="6" 
                          refX="0" refY="3" orient="auto">
                    <polygon points="0 0, 6 3, 0 6" fill="#9400D3" />
                  </marker>
                </defs>
                {(() => {
                  // Calculate arc parameters
                  const centerX = cartX + cartWidth / 2;
                  const centerY = cartY;
                  const radius = 30;
                  const forceRatio = Math.min(Math.abs(displayForces[1]) / maxForceRange, 1);
                  const maxAngle = Math.PI * 2; // Full circle (360 degrees)
                  const arcAngle = forceRatio * maxAngle * 0.8; // Scale to 80% of full circle for visualization
                  
                  // Fix direction: positive torque = counterclockwise, negative = clockwise
                  const isCounterClockwise = displayForces[1] > 0;
                  
                  // Start angle (always start from top)
                  const startAngle = -Math.PI / 2; // Start at top (12 o'clock)
                  const endAngle = startAngle + (isCounterClockwise ? -arcAngle : arcAngle);
                  
                  // Calculate start and end points
                  const startX = centerX + radius * Math.cos(startAngle);
                  const startY = centerY + radius * Math.sin(startAngle);
                  const endX = centerX + radius * Math.cos(endAngle);
                  const endY = centerY + radius * Math.sin(endAngle);
                  
                  // Determine if we need a large arc (> 180 degrees)
                  const largeArcFlag = arcAngle > Math.PI ? 1 : 0;
                  const sweepFlag = isCounterClockwise ? 0 : 1;
                  
                  return (
                    <path 
                      d={`M ${startX} ${startY} 
                          A ${radius} ${radius} 0 ${largeArcFlag} ${sweepFlag} ${endX} ${endY}`}
                      stroke="#9400D3" 
                      strokeWidth="3"
                      fill="none"
                      markerEnd="url(#arrowhead-torque)"
                    />
                  );
                })()}
                {/* Torque label */}
                <text 
                  x={cartX + cartWidth / 2 + 45} 
                  y={cartY - 15} 
                  fontSize="10" 
                  fill="#9400D3"
                  fontFamily="Arial, sans-serif"
                  textAnchor="middle"
                  fontWeight="bold"
                >
                  τ={displayForces[1].toFixed(1)}Nm
                </text>
              </g>
            )}
          </g>
        )}
        
        {/* Position indicator - now shows absolute position */}
        <text 
          x={10} 
          y={30} 
          fontSize="12" 
          fill="#333"
          fontFamily="monospace"
        >
          Cart: {displayCartPosition.toFixed(2)}m (world)
        </text>
        <text 
          x={10} 
          y={50} 
          fontSize="12" 
          fill="#333"
          fontFamily="monospace"
        >
          Pole: {(displayPoleAngle * 180 / Math.PI).toFixed(1)}°
        </text>
        
        <text 
          x={10} 
          y={70} 
          fontSize="10" 
          fill="#666"
          fontFamily="monospace"
        >
          World Range: {minTrack}m to {maxTrack}m
        </text>
      </svg>
      </div>
    </div>
  );
};

// Main Visualisation component that can handle different types
interface VisualisationProps {
  type: 'cartpole' | 'pendulum' | 'other';
  coordinates: number[];
  forces?: number[];
  width?: number;
  height?: number;
  smoothTransition?: boolean;
  positionRange?: { min: number; max: number };
  forceRange?: { min: number; max: number };
}

const Visualisation: React.FC<VisualisationProps> = ({ 
  type, 
  coordinates, 
  forces,
  width, 
  height,
  smoothTransition = true,
  positionRange,
  forceRange
}) => {
  switch (type) {
    case 'cartpole':
      // For cart pole: coordinates[0] = cart position, coordinates[1] = pole angle
      return (
        <CartPole 
          cartPosition={coordinates[0] || 0}
          poleAngle={coordinates[1] || 0}
          forces={forces}
          width={width}
          height={height}
          smoothTransition={smoothTransition}
          positionRange={positionRange}
          forceRange={forceRange}
        />
      );
    
    default:
      return (
        <div className="p-4 border border-gray-300 rounded">
          <p>Visualisation for {type} not implemented yet</p>
          <p>Coordinates: {coordinates.join(', ')}</p>
        </div>
      );
  }
};

export default Visualisation;
export { CartPole };