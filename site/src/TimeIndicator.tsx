import React from "react";

interface TimeIndicatorProps {
  currentTime: number | undefined;
  data: any[];
  rectangle: {
    width: number;
    height: number;
    left: number;
    top: number;
  } | null;
}

const TimeIndicator: React.FC<TimeIndicatorProps> = ({ currentTime, data, rectangle }) => {
  if (currentTime === undefined || data.length === 0 || !rectangle) {
    return null;
  }
  
  const minTime = data[0].time;
  const maxTime = data[data.length - 1].time;
  const timeRange = maxTime - minTime;
  
  if (timeRange === 0) return null;
  
  // Calculate exact position within the chart area
  const timeRatio = (currentTime - minTime) / timeRange;
  
  // Now rectangle contains relative positions within the parent container
  const xPosition = rectangle.left + (timeRatio * rectangle.width);
  
  return (
    <div
      className="absolute w-0.5 bg-red-500 pointer-events-none z-20"
      style={{
        left: `${xPosition}px`,
        top: `${rectangle.top}px`,
        height: `${rectangle.height}px`,
      }}
    />
  );
};

export default React.memo(TimeIndicator);
