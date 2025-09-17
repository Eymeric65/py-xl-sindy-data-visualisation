import React, { useEffect, useState } from "react";
import InteractiveCurve from "./InteractiveCurve";
import TimeSlider from "./TimeSlider";
import Visualisation from "./Visualisation";

type CoordinateData = {
  [varName: string]: number[];
};

type SeriesData = {
  [coordinateName: string]: CoordinateData;
};

type VisualisationData = {
  time: number[][];
  series: SeriesData;
};

type VisualisationSeries = {
  [seriesName: string]: VisualisationData;
};

type ResultJson = {
  generation_settings?: {
    experiment_folder?: string;
  };
  visualisation_series: VisualisationSeries;
};

const App: React.FC = () => {
  const [availableFiles, setAvailableFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [availableVisualisationSeries, setAvailableVisualisationSeries] = useState<string[]>([]);
  const [selectedVisualisationSeries, setSelectedVisualisationSeries] = useState<string>("");
  const [data, setData] = useState<any[]>([]);
  const [groupedLines, setGroupedLines] = useState<{[varType: string]: {[coordinate: string]: string[]}}>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [simulationType, setSimulationType] = useState<string>("");
  const [fullJsonData, setFullJsonData] = useState<ResultJson | null>(null);

  // Load available files on mount
  useEffect(() => {
    // Fetch the files manifest
    fetch("results/files.json")
      .then(res => {
        if (!res.ok) {
          throw new Error("Could not fetch files manifest");
        }
        return res.json();
      })
      .then((manifest: { files: string[] }) => {
        setAvailableFiles(manifest.files);
        if (manifest.files.length > 0) {
          setSelectedFile(manifest.files[0]);
        }
      })
      .catch((error) => {
        console.error("Failed to load files manifest:", error);
        // Fallback to hardcoded file
        const fallbackFiles = ["0a25fa5db7bcb8cafb152f79f36db501.json"];
        setAvailableFiles(fallbackFiles);
        setSelectedFile(fallbackFiles[0]);
      });
  }, []);

  // Load data when file is selected
  useEffect(() => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);
    
    fetch(`results/${selectedFile}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load data");
        return res.json();
      })
      .then((json: ResultJson) => {
        const visualisationSeries = Object.keys(json.visualisation_series);
        setAvailableVisualisationSeries(visualisationSeries);
        if (visualisationSeries.length > 0 && !selectedVisualisationSeries) {
          setSelectedVisualisationSeries(visualisationSeries[0]);
        }
        
        // Extract simulation type from experiment_folder
        if (json.generation_settings?.experiment_folder) {
          const folderPath = json.generation_settings.experiment_folder;
          const simType = folderPath.split('/').pop() || "";
          setSimulationType(simType);
        }
        
        setFullJsonData(json);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [selectedFile]);

  // Process data when visualisation series is selected
  useEffect(() => {
    if (!selectedFile || !selectedVisualisationSeries) return;

    setLoading(true);
    
    fetch(`results/${selectedFile}`)
      .then(res => res.json())
      .then((json: ResultJson) => {
        const selectedData = json.visualisation_series[selectedVisualisationSeries];
        const timeArr = selectedData.time.map((t) => t[0]);
        
        // Create flat data and group by variable type with coordinates side by side
        const groupedByVar: {[varType: string]: {[coordinate: string]: string[]}} = {};
        const flatData = timeArr.map((t, i) => {
          const point: any = { time: t };
          
          // Process all coordinates for this visualisation series
          Object.entries(selectedData.series).forEach(([coordinateName, coordinateData]) => {
            Object.entries(coordinateData).forEach(([varName, arr]) => {
              const key = `${coordinateName}.${varName}`;
              point[key] = arr[i];
              
              // Group by variable type, then by coordinate
              if (!groupedByVar[varName]) groupedByVar[varName] = {};
              if (!groupedByVar[varName][coordinateName]) groupedByVar[varName][coordinateName] = [];
              if (!groupedByVar[varName][coordinateName].includes(key)) {
                groupedByVar[varName][coordinateName].push(key);
              }
            });
          });
          
          return point;
        });
        
        setData(flatData);
        setGroupedLines(groupedByVar);
        setCurrentIdx(0);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [selectedFile, selectedVisualisationSeries]);

  // Calculate position and force ranges for cart pole visualization
  const getPositionRange = () => {
    if (!data.length) return { min: -20, max: 20 };
    const positions = data.map(d => d['coor_0.qpos']).filter(p => typeof p === 'number');
    return {
      min: Math.min(...positions),
      max: Math.max(...positions)
    };
  };

  const getForceRange = () => {
    if (!data.length) return { min: -20, max: 20 };
    const cartForces = data.map(d => d['coor_0.forces']).filter(f => typeof f === 'number');
    const poleForces = data.map(d => d['coor_1.forces']).filter(f => typeof f === 'number');
    const allForces = [...cartForces, ...poleForces];
    return {
      min: Math.min(...allForces),
      max: Math.max(...allForces)
    };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-6">Time Series Data Visualizer</h1>
        
        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Data File:
              </label>
              <select 
                value={selectedFile} 
                onChange={(e) => setSelectedFile(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                {availableFiles.map(file => (
                  <option key={file} value={file}>{file}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Visualisation Series:
              </label>
              <select 
                value={selectedVisualisationSeries} 
                onChange={(e) => setSelectedVisualisationSeries(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                {availableVisualisationSeries.map(series => (
                  <option key={series} value={series}>{series}</option>
                ))}
              </select>
            </div>
          </div>
          
          {data.length > 0 && (
            <TimeSlider
              times={data.map((d) => d.time)}
              onChange={setCurrentIdx}
            />
          )}
        </div>

        {/* Simulation Visualization */}
        {!loading && !error && data.length > 0 && simulationType === 'cart_pole' && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <Visualisation 
              type="cartpole"
              coordinates={[
                data[currentIdx]?.['coor_0.qpos'] || 0,  // cart position
                data[currentIdx]?.['coor_1.qpos'] || 0   // pole angle
              ]}
              forces={[
                data[currentIdx]?.['coor_0.forces'] || 0,  // cart force
                data[currentIdx]?.['coor_1.forces'] || 0   // pole torque
              ]}
              positionRange={getPositionRange()}
              forceRange={getForceRange()}
              width={500}
              height={350}
            />
          </div>
        )}

        {/* Status */}
        {loading && <p className="text-center text-gray-600">Loading data...</p>}
        {error && <p className="text-center text-red-500">Error: {error}</p>}
        
        {/* Visualizations */}
        {!loading && !error && data.length > 0 && (
          <div className="space-y-6">
            {Object.entries(groupedLines).map(([varType, coordinateGroups]) => (
              <div key={varType} className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4 capitalize">
                  {varType} ({selectedVisualisationSeries})
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {Object.entries(coordinateGroups).map(([coordinateName, lines]) => (
                    <div key={coordinateName} className="space-y-2">
                      <h3 className="text-lg font-medium text-gray-700">
                        {coordinateName}
                      </h3>
                      <InteractiveCurve 
                        data={data} 
                        lines={lines} 
                        currentTime={data[currentIdx]?.time} 
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
