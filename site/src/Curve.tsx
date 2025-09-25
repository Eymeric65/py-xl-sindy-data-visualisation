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

  // Transform data and lines for relative mode
  const { processedData, processedLines } = React.useMemo(() => {
    if (!relative) {
      return { processedData: data, processedLines: lines };
    }

    // Find reference line (line without prefix, e.g., "coor_0.qpos")
    const referenceLine = lines.find(line => !line.includes('.') || line.split('.').length <= 2);
    
    if (!referenceLine) {
      // No reference line found, return original data
      return { processedData: data, processedLines: lines };
    }

    // Find other lines (lines with prefix, e.g., "abcd1234.coor_0.qpos")
    const otherLines = lines.filter(line => line !== referenceLine && line.split('.').length > 2);
    
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
          // Create a new line name for the relative difference
          const relativeName = `${line}_rel`;
          newPoint[relativeName] = otherValue - referenceValue;
        }
      });
      
      return newPoint;
    });

    // New lines list: only relative difference lines (no reference line)
    const relativeLines = otherLines.map(line => `${line}_rel`);

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
            <Tooltip />
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