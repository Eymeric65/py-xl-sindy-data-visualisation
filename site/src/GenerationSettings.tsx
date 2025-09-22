import React from "react";

type GenerationSettingsProps = {
  settings: any;
};

const GenerationSettings: React.FC<GenerationSettingsProps> = ({ settings }) => {
  const renderValue = (value: any, depth: number = 0): React.ReactNode => {
    const indent = depth * 20;
    
    if (value === null || value === undefined) {
      return <span className="text-gray-500">null</span>;
    }
    
    if (typeof value === "boolean") {
      return <span className="text-blue-600">{value.toString()}</span>;
    }
    
    if (typeof value === "number") {
      return <span className="text-green-600">{value}</span>;
    }
    
    if (typeof value === "string") {
      return <span className="text-orange-600">"{value}"</span>;
    }
    
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-gray-500">[]</span>;
      }
      
      return (
        <div>
          <span className="text-gray-700">[</span>
          {value.map((item, index) => (
            <div key={index} style={{ marginLeft: indent + 20 }}>
              <span className="text-gray-400">{index}:</span> {renderValue(item, depth + 1)}
              {index < value.length - 1 && <span className="text-gray-700">,</span>}
            </div>
          ))}
          <div style={{ marginLeft: indent }}>
            <span className="text-gray-700">]</span>
          </div>
        </div>
      );
    }
    
    if (typeof value === "object") {
      const entries = Object.entries(value);
      if (entries.length === 0) {
        return <span className="text-gray-500">{"{}"}</span>;
      }
      
      return (
        <div>
          <span className="text-gray-700">{"{"}</span>
          {entries.map(([key, val], index) => (
            <div key={key} style={{ marginLeft: indent + 20 }}>
              <span className="text-blue-800 font-medium">{key}:</span> {renderValue(val, depth + 1)}
              {index < entries.length - 1 && <span className="text-gray-700">,</span>}
            </div>
          ))}
          <div style={{ marginLeft: indent }}>
            <span className="text-gray-700">{"}"}</span>
          </div>
        </div>
      );
    }
    
    return <span className="text-red-500">{String(value)}</span>;
  };

  if (!settings) {
    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Generation Settings</h3>
        <p className="text-gray-500">No generation settings available</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-gray-700 mb-3">Generation Settings</h3>
      <div className="font-mono text-sm bg-white rounded border p-3 overflow-auto max-h-64">
        {renderValue(settings)}
      </div>
    </div>
  );
};

export default GenerationSettings;