import React, { useRef, useState, useEffect } from "react";
import Curve from "./Curve";
import TimeIndicator from "./TimeIndicator";

interface InteractiveCurveProps {
  data: any[];
  lines: string[];
  currentTime?: number;
}

const InteractiveCurve: React.FC<InteractiveCurveProps> = ({ data, lines, currentTime }) => {

  const ref = useRef<HTMLDivElement>(null);
  const [plotRect, setPlotRect] = useState<DOMRect | null>(null);

  // Function to update plot rectangle
  const updatePlotRect = () => {
    if (ref.current) {
      const plotArea = ref.current.querySelector(".recharts-cartesian-grid") as SVGElement | null;
      if (plotArea) {
        const newRect = plotArea.getBoundingClientRect();
        setPlotRect(newRect);
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
    if (ref.current) {
      resizeObserver.observe(ref.current);
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
    <div className="w-full flex justify-center mt-2" >
      <Curve data={data} lines={lines} containerRef={ref} />
      <TimeIndicator currentTime={currentTime} data={data} rectangle={plotRect} />
    </div>
  );

};

export default InteractiveCurve;
