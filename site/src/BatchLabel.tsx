import React from "react";

interface BatchLabelProps {
  viewBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  value?: string;
}

const BatchLabel: React.FC<BatchLabelProps> = ({ viewBox, value }) => {
  if (!viewBox || !value) return null;

  const { x, y } = viewBox;

  return (
    <g>
      <text
        x={x + 2}
        y={y + 25}
        fill="green"
        fontSize="10"
        fontWeight="500"
        transform={`rotate(-90, ${x + 2}, ${y + 10})`}
        textAnchor="end"
      >
        {value}
      </text>
    </g>
  );
};

export default BatchLabel;