import React, { useEffect, useState } from 'react';
import SlidingBackground from './SlidingBackground';
import CartPole from './CartPole';

// Define what a series IS
interface Series {
  cartPosition: number;
  poleAngle: number;
  forces: number[];
}

interface CartPoleVisualizationProps {
  cartPosition: number; // x position of the cart (reference, raw)
  poleAngle: number;    // angle of the pole in radians (reference, raw)
  forces?: number[];    // forces array [cart_force, pole_torque] (reference)
  otherSeries?: Array<{  // additional series to render as ghosts (raw)
    cartPosition: number;
    poleAngle: number;
    forces?: number[];
  }>;
  width?: number;       // canvas width
  height?: number;      // canvas height
  smoothTransition?: boolean; // enable smooth transitions
  positionRange?: { min: number; max: number };
  forceRange?: { min: number; max: number };
}

const CartPoleVisualization: React.FC<CartPoleVisualizationProps> = ({ 
  cartPosition, 
  poleAngle, 
  forces = [0, 0],
  otherSeries = [],
  width = 800, 
  height = 400,
  smoothTransition = true,
  positionRange,
  forceRange
}) => {
  // Build clean data structure: ALL series (reference first, then others)
  const rawAllSeries: Series[] = [
    {
      cartPosition,
      poleAngle,
      forces
    },
    ...otherSeries.map(s => ({
      cartPosition: s.cartPosition,
      poleAngle: s.poleAngle,
      forces: s.forces || [0, 0]
    }))
  ];

  // SINGLE state object containing ALL smoothed values
  const [smoothedAllSeries, setSmoothedAllSeries] = useState(rawAllSeries);
  
  // Track data update rate for adaptive smoothing
  const [lastUpdateTime, setLastUpdateTime] = useState(performance.now());
  const [dataUpdateRate, setDataUpdateRate] = useState(50); // Default to 50ms (20fps)

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

  // Track data update rate for adaptive smoothing
  useEffect(() => {
    const currentTime = performance.now();
    const timeSinceLastUpdate = currentTime - lastUpdateTime;
    
    // Update the data rate (with some smoothing to avoid jitter)
    setDataUpdateRate(prev => Math.min(prev * 0.8 + timeSinceLastUpdate * 0.2, 2000));
    setLastUpdateTime(currentTime);
  }, [cartPosition, poleAngle, otherSeries, forces]);

  // SINGLE animation loop that runs independently of data updates
  useEffect(() => {
    if (!smoothTransition) {
      setSmoothedAllSeries(rawAllSeries);
      return;
    }

    let animationId: number;
    
    const animate = () => {
      setSmoothedAllSeries(currentSmoothed => {
        // Get fresh target data by rebuilding rawAllSeries inside the animation
        const currentRawAllSeries: Series[] = [
          {
            cartPosition,
            poleAngle,
            forces
          },
          ...otherSeries.map(s => ({
            cartPosition: s.cartPosition,
            poleAngle: s.poleAngle,
            forces: s.forces || [0, 0]
          }))
        ];
        
        // Calculate adaptive smoothing factor based on data update rate
        const targetFrameTime = 1000 / 60; // 60fps = ~16.67ms per frame
        const dataFrameTime = dataUpdateRate; // actual ms between data updates
        
        // Calculate how many render frames we have per data update
        const framesPerDataUpdate = Math.max(1, dataFrameTime / targetFrameTime);
        
        // Better adaptive smoothing: use exponential decay that feels consistent
        const adaptiveSmoothingFactor = 1 / (framesPerDataUpdate*1.2); // + for extra smoothness
        
        // Smooth all series (including reference as first element)
        return currentSmoothed.map((current, index) => {
          const target = currentRawAllSeries[index];
          if (!target) return current;
          
          // Helper function for smooth interpolation
          const smoothValue = (currentVal: number, targetVal: number) => 
            currentVal + (targetVal - currentVal) * adaptiveSmoothingFactor;
          
          return {
            cartPosition: smoothValue(current.cartPosition, target.cartPosition),
            poleAngle: (() => {
              let targetAngle = target.poleAngle;
              const angleDiff = targetAngle - current.poleAngle;
              if (angleDiff > Math.PI) targetAngle -= 2 * Math.PI;
              if (angleDiff < -Math.PI) targetAngle += 2 * Math.PI;
              return smoothValue(current.poleAngle, targetAngle);
            })(),
            forces: current.forces.map((currentForce, forceIndex) => 
              smoothValue(currentForce, target.forces[forceIndex] || 0)
            )
          };
        });
      });
      
      // Always continue animating (never stops, always smoothing towards current target)
      animationId = requestAnimationFrame(animate);
    };
    
    animationId = requestAnimationFrame(animate);
    
    // Cleanup function to stop animation when component unmounts or smoothTransition changes
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [smoothTransition, cartPosition, poleAngle, forces, otherSeries, dataUpdateRate]); // Include dependencies so animation gets fresh data

  return (
    <div className="flex flex-col items-center w-full max-w-full">
      <h3 className="text-lg font-semibold mb-2">Cart Pole Visualization</h3>
      <div className="w-full max-w-4xl overflow-hidden">
        <svg 
          viewBox={`0 0 ${responsiveWidth} ${responsiveHeight}`}
          className="w-full h-auto border border-gray-300 bg-gradient-to-b from-sky-200 to-sky-50"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Sliding Background */}
          <SlidingBackground 
            cartPosition={smoothedAllSeries[0]?.cartPosition || 0}
            width={responsiveWidth}
            height={responsiveHeight}
            positionRange={positionRange}
          />
          
          {/* Ghost CartPoles (all series except reference) */}
          {smoothedAllSeries.slice(1).map((series: Series, index: number) => (
            <CartPole
              key={`ghost-${index}`}
              cartPosition={series.cartPosition}
              poleAngle={series.poleAngle}
              forces={series.forces}
              width={responsiveWidth}
              height={responsiveHeight}
              forceRange={forceRange}
              ghost={true}
              referenceCartPosition={smoothedAllSeries[0]?.cartPosition || 0}
            />
          ))}
          
          {/* Main CartPole (reference - first in array) */}
          {smoothedAllSeries[0] && (
            <CartPole
              cartPosition={smoothedAllSeries[0].cartPosition}
              poleAngle={smoothedAllSeries[0].poleAngle}
              forces={smoothedAllSeries[0].forces}
              width={responsiveWidth}
              height={responsiveHeight}
              forceRange={forceRange}
              referenceCartPosition={smoothedAllSeries[0].cartPosition}
            />
          )}
          
          {/* World Range indicator */}
          <text 
            x={10} 
            y={responsiveHeight - 20} 
            fontSize="10" 
            fill="#666"
            fontFamily="monospace"
          >
            World Range: {minTrack}m to {maxTrack}m
          </text>
          
          {/* Data Update Rate indicator for debugging */}
          <text 
            x={10} 
            y={responsiveHeight - 5} 
            fontSize="10" 
            fill="#666"
            fontFamily="monospace"
          >
            Data Rate: {dataUpdateRate.toFixed(1)}ms ({(1000/dataUpdateRate).toFixed(1)}fps)
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
  dataPoint?: any; // Current data point with all series
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
  dataPoint,
  width, 
  height,
  smoothTransition = true,
  positionRange,
  forceRange
}) => {
  switch (type) {
    case 'cartpole':
      // Extract other series data from dataPoint
      const otherSeries: Array<{cartPosition: number; poleAngle: number; forces?: number[]}> = [];
      
      if (dataPoint) {
        // Find all series prefixes (exclude reference data)
        const allKeys = Object.keys(dataPoint);
        const seriesPrefixes = new Set<string>();
        
        allKeys.forEach(key => {
          // Look for keys like "prefix.coor_0.qpos" (but not direct "coor_0.qpos")
          const parts = key.split('.');
          if (parts.length === 3 && parts[1].startsWith('coor_') && !key.startsWith('coor_')) {
            seriesPrefixes.add(parts[0]);
          }
        });
        
        // Extract data for each series
        seriesPrefixes.forEach(prefix => {
          const cartPosition = dataPoint[`${prefix}.coor_0.qpos`] || 0;
          const poleAngle = dataPoint[`${prefix}.coor_1.qpos`] || 0;
          const cartForce = dataPoint[`${prefix}.coor_0.forces`] || 0;
          const poleForce = dataPoint[`${prefix}.coor_1.forces`] || 0;
          
          otherSeries.push({
            cartPosition,
            poleAngle,
            forces: [cartForce, poleForce]
          });
        });
      }
      
      // For cart pole: coordinates[0] = cart position, coordinates[1] = pole angle
      return (
        <CartPoleVisualization 
          cartPosition={coordinates[0] || 0}
          poleAngle={coordinates[1] || 0}
          forces={forces}
          otherSeries={otherSeries}
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
export { CartPole, CartPoleVisualization };