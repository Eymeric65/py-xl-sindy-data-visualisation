import React, { useEffect, useState } from "react";
import InteractiveCurve from "./InteractiveCurve";
import TimeSlider from "./TimeSlider";
import Visualisation from "./Visualisation";
import GenerationSettings from "./GenerationSettings";
import SolutionTables from "./SolutionTables";

type CoordinateData = {
  [varName: string]: number[];
};

type SeriesData = {
  [coordinateName: string]: CoordinateData;
};

type VisualisationData = {
  time: number[];
  series: SeriesData;
  reference?: boolean;
  solution?: any;
};

type GroupData = {
  data: {
    [dataName: string]: VisualisationData;
  };
  batch_starting_times?: number[];
};

type VisualisationGroups = {
  [groupName: string]: GroupData;
};

type ResultJson = {
  generation_settings?: {
    experiment_folder?: string;
  };
  visualisation: VisualisationGroups;
};

const App: React.FC = () => {
  const [availableFiles, setAvailableFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [availableGroups, setAvailableGroups] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>("");
  const [data, setData] = useState<any[]>([]);
  const [groupedLines, setGroupedLines] = useState<{[varType: string]: {[coordinate: string]: string[]}}>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [simulationType, setSimulationType] = useState<string>("");
  const [batchStartTimes, setBatchStartTimes] = useState<number[]>([]);
  const [generationSettings, setGenerationSettings] = useState<any>(null);
  const [allGroupsData, setAllGroupsData] = useState<VisualisationGroups>({});

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
        const groups = Object.keys(json.visualisation);
        setAvailableGroups(groups);
        if (groups.length > 0 && !selectedGroup) {
          setSelectedGroup(groups[0]);
        }
        
        // Store all groups data for solution tables
        setAllGroupsData(json.visualisation);
        
        // Set generation settings
        setGenerationSettings(json.generation_settings || null);
        
        // Extract simulation type from experiment_folder
        if (json.generation_settings?.experiment_folder) {
          const folderPath = json.generation_settings.experiment_folder;
          const simType = folderPath.split('/').pop() || "";
          setSimulationType(simType);
        }
        
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [selectedFile]);

  // Process data when group is selected
  useEffect(() => {
    if (!selectedFile || !selectedGroup) return;

    setLoading(true);
    
    fetch(`results/${selectedFile}`)
      .then(res => res.json())
      .then((json: ResultJson) => {
        const groupData = json.visualisation[selectedGroup];
        
        // Set batch starting times if available
        if (groupData.batch_starting_times) {
          setBatchStartTimes(groupData.batch_starting_times);
        } else {
          setBatchStartTimes([]);
        }
        
        // Get the first (and likely only) data entry in the group
        const dataKeys = Object.keys(groupData.data);
        if (dataKeys.length === 0) {
          setError("No data found in selected group");
          setLoading(false);
          return;
        }
        
        const selectedData = groupData.data[dataKeys[0]];
        const timeArr = selectedData.time;
        
        // Create flat data and group by variable type with coordinates side by side
        const groupedByVar: {[varType: string]: {[coordinate: string]: string[]}} = {};
        const flatData = timeArr.map((t: number, i: number) => {
          const point: any = { time: t };
          
          // Process all coordinates for this group
          Object.entries(selectedData.series).forEach(([coordinateName, coordinateData]) => {
            Object.entries(coordinateData as CoordinateData).forEach(([varName, arr]) => {
              const key = `${coordinateName}.${varName}`;
              point[key] = (arr as number[])[i];
              
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
  }, [selectedFile, selectedGroup]);

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
    <div className="min-h-screen bg-gray-50">
      {/* Enhanced Sticky Header */}
      <header className="sticky top-0 z-50 bg-white shadow-lg border-b border-gray-200 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* App Title with Icon */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-gray-800 tracking-tight">
                Time Series Data Visualizer
              </h1>
            </div>
            
            {/* Enhanced Controls */}
            <div className="flex items-center space-x-6 flex-1 justify-end">
              {/* File Selection */}
              <div className="flex items-center space-x-3">
                <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                  Data File
                </label>
                <select 
                  value={selectedFile} 
                  onChange={(e) => setSelectedFile(e.target.value)}
                  className="text-sm px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 min-w-[140px] hover:border-gray-400 shadow-sm"
                >
                  {availableFiles.map(file => (
                    <option key={file} value={file}>{file}</option>
                  ))}
                </select>
              </div>
              
              {/* Group Selection */}
              <div className="flex items-center space-x-3">
                <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                  Group
                </label>
                <select 
                  value={selectedGroup} 
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  className="text-sm px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 min-w-[140px] hover:border-gray-400 shadow-sm"
                >
                  {availableGroups.map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          
          {/* Enhanced Time Slider */}
          {data.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="bg-gray-50 rounded-lg p-3">
                <TimeSlider
                  times={data.map((d) => Number(d.time))}
                  onChange={setCurrentIdx}
                />
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">

        {/* Generation Settings Section */}
        {generationSettings && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <GenerationSettings settings={generationSettings} />
              </div>
              <div>
                {/* Right half - can be used for additional info later */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">Data Summary</h3>
                  {data.length > 0 && (
                    <div className="text-sm text-gray-600">
                      <p>Total data points: {data.length}</p>
                      <p>Simulation type: {simulationType}</p>
                      {batchStartTimes.length > 0 && (
                        <p>Batches: {batchStartTimes.length}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

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

        {/* Solution Analysis Tables */}
        {!loading && !error && selectedGroup && allGroupsData[selectedGroup] && (
          <SolutionTables groups={{ [selectedGroup]: allGroupsData[selectedGroup] }} />
        )}

        {/* Status */}
        {loading && <p className="text-center text-gray-600">Loading data...</p>}
        {error && <p className="text-center text-red-500">Error: {error}</p>}
        
        {/* Visualizations */}
        {!loading && !error && data.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              Data Visualization ({selectedGroup})
              {batchStartTimes.length > 0 && (
                <span className="text-sm text-gray-500 ml-2">
                  - {batchStartTimes.length} batches
                </span>
              )}
            </h2>
            <div className="space-y-6">
              {Object.entries(groupedLines).map(([varType, coordinateGroups]) => (
                <div key={varType}>
                  <h3 className="text-lg font-medium text-gray-800 mb-3 capitalize border-b border-gray-200 pb-2">
                    {varType}
                  </h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-4">
                    {Object.entries(coordinateGroups).map(([coordinateName, lines]) => (
                      <div key={coordinateName} className="space-y-2">
                        <h4 className="text-md font-medium text-gray-700">
                          {coordinateName}
                        </h4>
                        <InteractiveCurve 
                          data={data} 
                          lines={lines} 
                          currentTime={data[currentIdx]?.time} 
                          batchStartTimes={batchStartTimes}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
