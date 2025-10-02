import React from "react";
import "./zindex.css";
import BatchLabel from "./BatchLabel";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

type CurveProps = {
  lines: string[];
  data: any[];
  containerRef: React.Ref<HTMLDivElement> | undefined;
  batchStartTimes?: number[];
  relative?: boolean;
};

const Curve: React.FC<CurveProps> = ({ lines,data,containerRef,batchStartTimes, relative = false })=> {

  // Helper function to get display name for legend (only ranking number)
  const getDisplayName = (line: string): string => {
    if (line.includes('_rel')) {
      // For relative lines, just show the number with "rel"
      return line; // e.g., "1_rel", "2_rel"
    }
    
    const parts = line.split('.');
    if (parts.length > 2 && !isNaN(parseInt(parts[0]))) {
      // For ranking lines, show only the number
      return parts[0]; // e.g., "1", "2", "3"
    }
    
    // For reference lines, show as-is
    return line;
  };

  // Transform data and lines for relative mode
  const { processedData, processedLines } = React.useMemo(() => {
    if (!relative) {
      return { processedData: data, processedLines: lines };
    }

    // Find reference line (line without ranking number prefix, e.g., "coor_0.qpos")
    const referenceLine = lines.find(line => {
      const parts = line.split('.');
      // Reference line doesn't start with a number or has no dots
      return parts.length <= 2 || isNaN(parseInt(parts[0]));
    });
    
    if (!referenceLine) {
      // No reference line found, return original data
      return { processedData: data, processedLines: lines };
    }

    // Find other lines (lines with ranking number prefix, e.g., "1.coor_0.qpos", "2.coor_0.qpos")
    const otherLines = lines.filter(line => {
      if (line === referenceLine) return false;
      const parts = line.split('.');
      // Other lines start with a number (ranking)
      return parts.length > 2 && !isNaN(parseInt(parts[0]));
    });
    
    if (otherLines.length === 0) {
      // No other lines to make relative, return original data
      return { processedData: data, processedLines: lines };
    }

    // Transform data to show relative differences
    const transformedData = data.map(point => {
      const newPoint = { ...point };
      const referenceValue = point[referenceLine];
      
      // Create relative lines by subtracting reference from each other line
      otherLines.forEach(line => {
        const otherValue = point[line];
        if (typeof referenceValue === 'number' && typeof otherValue === 'number') {
          // Extract ranking number from line (e.g., "1" from "1.coor_0.qpos")
          const rankingNumber = line.split('.')[0];
          // Create a new line name using the ranking number with _rel suffix
          const relativeName = `${rankingNumber}_rel`;
          newPoint[relativeName] = otherValue - referenceValue;
        }
      });
      
      return newPoint;
    });

    // New lines list: only relative difference lines using ranking numbers (no reference line)
    const relativeLines = otherLines.map(line => `${line.split('.')[0]}_rel`);

    return { 
      processedData: transformedData, 
      processedLines: relativeLines 
    };
  }, [data, lines, relative]);

  return (
    <div className="w-full max-w-full h-[250px] bg-white rounded shadow p-4 relative">
      <div ref={containerRef} className="w-full h-full" style={{ width: '100%', height: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={processedData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" type="number" domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              labelFormatter={(value) => `Time: ${value}`}
              formatter={(value, _name, props) => {
                // Use the display name for tooltip
                const displayName = getDisplayName(props.dataKey as string);
                return [value, displayName];
              }}
            />
            <Legend />
            {batchStartTimes?.map((batchTime, idx) => (
              <ReferenceLine 
                key={`batch-${idx}`}
                x={batchTime} 
                stroke="green" 
                strokeDasharray="3 3"
                label={<BatchLabel value={`Batch ${idx + 1}`} />}
              />
            ))}
            {processedLines.map((line, idx) => (
              <Line
                key={line}
                type="monotone"
                dataKey={line}
                name={getDisplayName(line)}
                stroke={`hsl(${(idx * 47) % 360}, 70%, 50%)`}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

Curve.displayName = 'Curve';

export default React.memo(Curve);