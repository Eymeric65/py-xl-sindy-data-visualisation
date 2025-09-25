import React from 'react';

interface CartPoleProps {
  cartPosition: number; // x position of the cart (ALREADY SMOOTHED)
  poleAngle: number;    // angle of the pole in radians (ALREADY SMOOTHED)
  forces?: number[];    // forces array [cart_force, pole_torque] (ALREADY SMOOTHED)
  width: number;        // canvas width
  height: number;       // canvas height
  forceRange?: { min: number; max: number };
  ghost?: boolean;      // render as ghost (grayscale, low opacity, no forces)
  referenceCartPosition?: number; // reference cart position for camera offset
}

const CartPole: React.FC<CartPoleProps> = ({ 
  cartPosition, 
  poleAngle, 
  forces = [0, 0],
  width, 
  height,
  forceRange,
  ghost = false,
  referenceCartPosition = 0
}) => {
  // Force scaling - use provided range or defaults
  const minForce = forceRange?.min ?? -20; // minimum force/torque
  const maxForce = forceRange?.max ?? 20;  // maximum force/torque
  const maxForceRange = Math.max(Math.abs(minForce), Math.abs(maxForce));

  // Color scheme - normal vs ghost
  const opacity = ghost ? 0.3 : 1.0;
  const colors = ghost ? {
    // Grayscale ghost colors
    shadow: "rgba(100,100,100,0.1)",
    cartBody: "#888888",
    cartStroke: "#666666", 
    cartHandle: "#999999",
    wheel: "#777777",
    wheelStroke: "#555555",
    wheelSpokes: "#555555",
    pole: "#999999",
    poleStroke: "#777777",
    joint: "#888888",
    jointStroke: "#666666",
    centerMass: "#999999",
    text: "#666666"
  } : {
    // Normal bright colors
    shadow: "rgba(0,0,0,0.2)",
    cartBody: "#FF6B6B",
    cartStroke: "#E55454",
    cartHandle: "#FF8E8E", 
    wheel: "#4A4A4A",
    wheelStroke: "#2A2A2A",
    wheelSpokes: "#2A2A2A",
    pole: "#8B4513",
    poleStroke: "#CD853F",
    joint: "#FFD700",
    jointStroke: "#FFA500",
    centerMass: "#FFFF99",
    text: "#333"
  };

  // Constants for rendering
  const scale = 100; // pixels per meter
  const centerX = width / 2;
  const centerY = height * 0.65;
  
  // Ground and track positioning  
  const groundY = centerY + 40;
  const trackY = groundY - 5;
  
  // Calculate cart screen position relative to reference (camera) position
  const cameraOffset = -referenceCartPosition * scale;
  const cartScreenX = centerX + (cartPosition * scale) + cameraOffset;
  
  // Cart properties - positioned based on world position
  const cartWidth = 60;
  const cartHeight = 30;
  const cartX = cartScreenX - cartWidth / 2;
  const cartY = trackY - cartHeight;
  
  // Pole properties - we'll use transform for rotation instead of calculating endpoints
  const poleLength = 80;
  const poleWidth = 6;
  const poleAngleDegrees = (-poleAngle * 180) / Math.PI; // Convert to degrees for SVG transform
  
  // Wheel properties
  const wheelRadius = 12;
  const wheelY = cartY + cartHeight;
  
  // Calculate wheel rotation based on cart movement
  const wheelRotation = (cartPosition / (wheelRadius * 2 * Math.PI / scale)) * 360;

  return (
    <g>
      {/* Cart shadow */}
      <ellipse 
        cx={cartX + cartWidth / 2 } 
        cy={wheelY + wheelRadius} 
        rx={cartWidth / 2 + 5} 
        ry="8"
        fill={colors.shadow}
        opacity={opacity}
      />
      
      {/* Entire cart system with transform-based positioning */}
      <g transform={`translate(${cartScreenX - centerX}, 0)`}>
        {/* Cart body */}
        <rect 
          x={centerX - cartWidth / 2} 
          y={cartY} 
          width={cartWidth} 
          height={cartHeight}
          fill={colors.cartBody}
          stroke={colors.cartStroke}
          strokeWidth="2"
          rx="5"
          opacity={opacity}
        />
        
        {/* Cart details */}
        <rect 
          x={centerX - cartWidth / 2 + 5} 
          y={cartY + 5} 
          width={cartWidth - 10} 
          height={cartHeight - 10}
          fill={colors.cartHandle}
          rx="3"
          opacity={opacity}
        />
        
        {/* Wheels with rotation */}
        <g>
          {/* Wheel 1 */}
          <circle 
            cx={centerX - cartWidth / 2 + 15} 
            cy={wheelY} 
            r={wheelRadius}
            fill={colors.wheel}
            stroke={colors.wheelStroke}
            strokeWidth="2"
            opacity={opacity}
          />
          <g transform={`rotate(${wheelRotation} ${centerX - cartWidth / 2 + 15} ${wheelY})`} opacity={opacity}>
            <line x1={centerX - cartWidth / 2 + 15 - 6} y1={wheelY} x2={centerX - cartWidth / 2 + 15 + 6} y2={wheelY} stroke={colors.wheelSpokes} strokeWidth="2" />
            <line x1={centerX - cartWidth / 2 + 15} y1={wheelY - 6} x2={centerX - cartWidth / 2 + 15} y2={wheelY + 6} stroke={colors.wheelSpokes} strokeWidth="2" />
            <line x1={centerX - cartWidth / 2 + 15 - 4} y1={wheelY - 4} x2={centerX - cartWidth / 2 + 15 + 4} y2={wheelY + 4} stroke={colors.wheelSpokes} strokeWidth="1" />
            <line x1={centerX - cartWidth / 2 + 15 - 4} y1={wheelY + 4} x2={centerX - cartWidth / 2 + 15 + 4} y2={wheelY - 4} stroke={colors.wheelSpokes} strokeWidth="1" />
          </g>
          
          {/* Wheel 2 */}
          <circle 
            cx={centerX + cartWidth / 2 - 15} 
            cy={wheelY} 
            r={wheelRadius}
            fill={colors.wheel}
            stroke={colors.wheelStroke}
            strokeWidth="2"
            opacity={opacity}
          />
          <g transform={`rotate(${wheelRotation} ${centerX + cartWidth / 2 - 15} ${wheelY})`} opacity={opacity}>
            <line x1={centerX + cartWidth / 2 - 15 - 6} y1={wheelY} x2={centerX + cartWidth / 2 - 15 + 6} y2={wheelY} stroke={colors.wheelSpokes} strokeWidth="2" />
            <line x1={centerX + cartWidth / 2 - 15} y1={wheelY - 6} x2={centerX + cartWidth / 2 - 15} y2={wheelY + 6} stroke={colors.wheelSpokes} strokeWidth="2" />
            <line x1={centerX + cartWidth / 2 - 15 - 4} y1={wheelY - 4} x2={centerX + cartWidth / 2 - 15 + 4} y2={wheelY + 4} stroke={colors.wheelSpokes} strokeWidth="1" />
            <line x1={centerX + cartWidth / 2 - 15 - 4} y1={wheelY + 4} x2={centerX + cartWidth / 2 - 15 + 4} y2={wheelY - 4} stroke={colors.wheelSpokes} strokeWidth="1" />
          </g>
        </g>
        
        {/* Pole with transform-based rotation */}
        <g transform={`rotate(${poleAngleDegrees} ${centerX} ${cartY})`}>
          {/* Main pole line */}
          <line 
            x1={centerX} 
            y1={cartY} 
            x2={centerX} 
            y2={cartY - poleLength}
            stroke={colors.pole}
            strokeWidth={poleWidth}
            strokeLinecap="round"
            opacity={opacity}
          />
          
          {/* Pole outline for better visibility */}
          <line 
            x1={centerX} 
            y1={cartY} 
            x2={centerX} 
            y2={cartY - poleLength}
            stroke={colors.poleStroke}
            strokeWidth={poleWidth - 2}
            strokeLinecap="round"
            opacity={opacity * 0.6}
          />
          
          {/* Pole end (small circle at the top) */}
          <circle 
            cx={centerX} 
            cy={cartY - poleLength} 
            r="8"
            fill={colors.joint}
            stroke={colors.jointStroke}
            strokeWidth="2"
            opacity={opacity}
          />
          
          {/* Pole tip highlight */}
          <circle 
            cx={centerX - 2} 
            cy={cartY - poleLength - 2} 
            r="3"
            fill={colors.centerMass}
            opacity={opacity}
          />
        </g>
        
        {/* Joint (connection point) */}
        <circle 
          cx={centerX} 
          cy={cartY} 
          r="8"
          fill={colors.joint}
          stroke={colors.jointStroke}
          strokeWidth="2"
          opacity={opacity}
        />
        
        {/* Pivot point */}
        <circle 
          cx={centerX} 
          cy={cartY} 
          r="4"
          fill={colors.text}
          opacity={opacity}
        />
      </g>
      
      {/* Force visualization - only show if not ghost */}
      {!ghost && forces && (forces[0] !== 0 || forces[1] !== 0) && (
        <g transform={`translate(${cartScreenX - centerX}, 0)`}>
          {/* Cart force arrow (horizontal) */}
          {forces[0] !== 0 && (
            <g>
              {/* Force arrow for cart */}
              <defs>
                <marker id="arrowhead-cart" markerWidth="10" markerHeight="7" 
                        refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#FF4500" />
                </marker>
              </defs>
              <line 
                x1={centerX} 
                y1={cartY + cartHeight / 2} 
                x2={centerX + Math.sign(forces[0]) * Math.min((Math.abs(forces[0]) / maxForceRange) * 80, 80)} 
                y2={cartY + cartHeight / 2}
                stroke="#FF4500" 
                strokeWidth="4"
                markerEnd="url(#arrowhead-cart)"
              />
              {/* Force label */}
              <text 
                x={centerX + Math.sign(forces[0]) * (Math.min((Math.abs(forces[0]) / maxForceRange) * 80, 80) / 2)} 
                y={cartY + cartHeight / 2 - 10} 
                fontSize="10" 
                fill="#FF4500"
                fontFamily="Arial, sans-serif"
                textAnchor="middle"
                fontWeight="bold"
              >
                F={forces[0].toFixed(1)}N
              </text>
            </g>
          )}
          
          {/* Pole torque arc arrow */}
          {forces[1] !== 0 && (
            <g>
              <defs>
                <marker id="arrowhead-torque" markerWidth="6" markerHeight="6" 
                        refX="0" refY="3" orient="auto">
                  <polygon points="0 0, 6 3, 0 6" fill="#9400D3" />
                </marker>
              </defs>
              {(() => {
                // Calculate arc parameters
                const torqueCenterX = centerX;
                const torqueCenterY = cartY;
                const radius = 30;
                const forceRatio = Math.min(Math.abs(forces[1]) / maxForceRange, 1);
                const maxAngle = Math.PI * 2; // Full circle (360 degrees)
                const arcAngle = forceRatio * maxAngle * 0.8; // Scale to 80% of full circle for visualization
                
                // Fix direction: positive torque = counterclockwise, negative = clockwise
                const isCounterClockwise = forces[1] < 0;
                
                // Start angle (always start from top)
                const startAngle = -Math.PI / 2; // Start at top (12 o'clock)
                const endAngle = startAngle + (isCounterClockwise ? -arcAngle : arcAngle);
                
                // Calculate start and end points
                const startX = torqueCenterX + radius * Math.cos(startAngle);
                const startY = torqueCenterY + radius * Math.sin(startAngle);
                const endX = torqueCenterX + radius * Math.cos(endAngle);
                const endY = torqueCenterY + radius * Math.sin(endAngle);
                
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
                x={centerX + 45} 
                y={cartY - 15} 
                fontSize="10" 
                fill="#9400D3"
                fontFamily="Arial, sans-serif"
                textAnchor="middle"
                fontWeight="bold"
              >
                τ={forces[1].toFixed(1)}Nm
              </text>
            </g>
          )}
        </g>
      )}      {/* Position indicator - now shows absolute position */}
      <text 
        x={10} 
        y={30} 
        fontSize="12" 
        fill={colors.text}
        fontFamily="monospace"
        opacity={opacity}
      >
        Cart: {cartPosition.toFixed(2)}m (world)
      </text>
      <text 
        x={10} 
        y={50} 
        fontSize="12" 
        fill={colors.text}
        fontFamily="monospace"
        opacity={opacity}
      >
        Pole: {(poleAngle * 180 / Math.PI).toFixed(1)}°
      </text>
    </g>
  );
};

export default CartPole;