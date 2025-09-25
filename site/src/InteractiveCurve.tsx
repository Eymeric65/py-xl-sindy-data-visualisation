import React, { useRef, useState, useEffect } from "react";
import Curve from "./Curve";
import TimeIndicator from "./TimeIndicator";

interface InteractiveCurveProps {
  data: any[];
  lines: string[];
  currentTime?: number;
  batchStartTimes?: number[];
  relative?: boolean;
}

const InteractiveCurve: React.FC<InteractiveCurveProps> = ({ data, lines, currentTime, batchStartTimes, relative = false }) => {

  const containerRef = useRef<HTMLDivElement>(null);
  const curveRef = useRef<HTMLDivElement>(null);
  const [plotRect, setPlotRect] = useState<DOMRect | null>(null);

  // Function to update plot rectangle
  const updatePlotRect = () => {
    if (curveRef.current) {
      const plotArea = curveRef.current.querySelector(".recharts-cartesian-grid") as SVGElement | null;
      if (plotArea) {
        // Get the chart container's bounding rect
        const containerRect = containerRef.current?.getBoundingClientRect();
        const plotAreaRect = plotArea.getBoundingClientRect();
        
        if (containerRect) {
          // Calculate relative position within the container
          const relativeRect = {
            left: plotAreaRect.left - containerRect.left,
            top: plotAreaRect.top - containerRect.top,
            width: plotAreaRect.width,
            height: plotAreaRect.height,
          };
          
          setPlotRect(relativeRect as DOMRect);
        }
      }
    }
  };

  // Effect to set up observers and event listeners
  useEffect(() => {
    // Set up ResizeObserver
    const resizeObserver = new ResizeObserver(() => {
      updatePlotRect();
    });

    // Window event handlers
    const handleResize = () => {
      setTimeout(updatePlotRect, 50);
    };

    // Add event listeners
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    // Observe the container
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    
    // Also observe the curve container for chart changes
    if (curveRef.current) {
      resizeObserver.observe(curveRef.current);
    }

    // Cleanup
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  // Effect to update when data changes and ensure chart is rendered
  useEffect(() => {
    const timer = setTimeout(() => {
      updatePlotRect();
    }, 200); // Give chart time to render

    return () => clearTimeout(timer);
  }, [data, lines]);

  return (
    <div className="w-full flex justify-center mt-2 relative overflow-hidden">
      <div ref={containerRef} className="relative w-full max-w-full" style={{ width: '100%' }}>
        <Curve data={data} lines={lines} containerRef={curveRef} batchStartTimes={batchStartTimes} relative={relative} />
        <TimeIndicator currentTime={currentTime} data={data} rectangle={plotRect} />
      </div>
    </div>
  );

};

export default InteractiveCurve;
