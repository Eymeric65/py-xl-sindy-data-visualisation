import React from "react";
import "./zindex.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type CurveProps = {
  lines: string[];
  data: any[];
  containerRef: React.Ref<HTMLDivElement> | undefined;
};

const Curve: React.FC<CurveProps> = ({ lines,data,containerRef }) => {

  return (
    <div className="w-full max-w-full h-[250px] bg-white rounded shadow p-4 relative">
      <div ref={containerRef} className="w-full h-full" style={{ width: '100%', height: '100%', minWidth: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" type="number" domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {lines.map((line, idx) => (
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