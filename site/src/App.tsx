import React, { useEffect, useState, useMemo } from "react";
import InteractiveCurve from "./InteractiveCurve";
import TimeSlider from "./TimeSlider";
import Visualisation from "./Visualisation";
import GenerationSettings from "./GenerationSettings";
import SolutionTables from "./SolutionTables";
import FileExplorer from "./FileExplorer";
import SolutionControlTable from "./SolutionControlTable";
import PresentationSlides from "./PresentationSlides";
import { createSolutionRanking, transformLinesWithRanking, transformDataWithRanking } from './solutionRanking';
import type { GroupData as RankingGroupData } from './solutionRanking';
import type { 
  Experiment, 
  TrajectoryGroup, 
  FlatDataPoint, 
  GroupedLines 
} from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'data' | 'slides'>('data');
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [availableGroups, setAvailableGroups] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>("");
  const [data, setData] = useState<FlatDataPoint[]>([]);
  const [groupedLines, setGroupedLines] = useState<GroupedLines>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [simulationType, setSimulationType] = useState<string>("");
  const [batchStartTimes, setBatchStartTimes] = useState<number[]>([]);
  const [generationParams, setGenerationParams] = useState<any | null>(null);
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [relativeMode, setRelativeMode] = useState<boolean>(false);
  const [hiddenSolutions, setHiddenSolutions] = useState<Set<string>>(new Set());
  
  // Create ranking map for consistent solution numbering across all components
  const rankingMap = useMemo(() => {
    if (!experiment) return new Map();
    
    // Convert experiment structure to format expected by ranking function
    const groupsForRanking: { [groupName: string]: RankingGroupData } = {};
    
    ['validation_group', 'training_group'].forEach(groupKey => {
      const group = experiment.data[groupKey as keyof typeof experiment.data] as TrajectoryGroup;
      const dataObj: { [key: string]: any } = {};
      
      group.trajectories.forEach(traj => {
        if (!traj.reference && traj.solutions && traj.regression_result) {
          dataObj[traj.name] = {
            solution: {},
            extra_info: {
              noise_level: traj.regression_result.regression_parameters.noise_level,
              optimization_function: traj.regression_result.regression_parameters.optimization_function,
              regression_type: traj.regression_result.regression_parameters.regression_type,
              valid: traj.regression_result.valid,
              regression_time: traj.regression_result.regression_time,
              results: {
                RMSE_acceleration: traj.regression_result.RMSE_acceleration
              }
            }
          };
          
          // Add solutions
          traj.solutions.forEach(sol => {
            dataObj[traj.name].solution[sol.mode_solution] = {
              vector: sol.solution_vector,
              label: sol.solution_label
            };
          });
        }
      });
      
      groupsForRanking[groupKey] = { data: dataObj };
    });
    
    return createSolutionRanking(groupsForRanking);
  }, [experiment]);

  // Handle solution visibility toggle
  const handleSolutionToggle = (solutionId: string, isVisible: boolean) => {
    setHiddenSolutions(prev => {
      const newSet = new Set(prev);
      if (isVisible) {
        newSet.delete(solutionId);
      } else {
        newSet.add(solutionId);
      }
      console.log(`Solution ${solutionId} is now ${isVisible ? 'visible' : 'hidden'}. Hidden solutions:`, Array.from(newSet));
      return newSet;
    });
  };

  // Handle file selection from FileExplorer
  const handleFileSelect = (filename: string) => {
    setSelectedFile(filename);
  };

  // Set a default file if none selected (pick random from manifest)
  useEffect(() => {
    if (!selectedFile) {
      fetch('results/files.json')
        .then(res => {
          if (!res.ok) throw new Error('Failed to load files manifest');
          return res.json();
        })
        .then(data => {
          if (data && data.files && data.files.length > 0) {
            // Pick a random file from the manifest
            const randomIndex = Math.floor(Math.random() * data.files.length);
            const randomFile = data.files[randomIndex];
            setSelectedFile(randomFile.filename);
          }
        })
        .catch(err => {
          console.error('Failed to load files.json:', err);
          setError('Failed to load experiment list');
        });
    }
  }, [selectedFile]);

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
      .then((json: Experiment) => {
        // Store the experiment
        setExperiment(json);
        
        // Set available groups
        const groups = ['validation_group', 'training_group'];
        setAvailableGroups(groups);
        if (groups.length > 0 && !selectedGroup) {
          setSelectedGroup(groups[0]);
        }
        
        // Set generation params
        setGenerationParams(json.generation_params);
        
        // Extract simulation type from experiment_folder
        if (json.generation_params?.experiment_folder) {
          const folderPath = json.generation_params.experiment_folder;
          const simType = folderPath.split('/').pop() || "";
          setSimulationType(simType);
        }
        
        // Initialize hiddenSolutions with all solution IDs (hide all by default)
        const allSolutionIds = new Set<string>();
        ['validation_group', 'training_group'].forEach(groupKey => {
          const group = json.data[groupKey as keyof typeof json.data] as TrajectoryGroup;
          group.trajectories.forEach(traj => {
            if (!traj.reference && traj.solutions) {
              const solutionId = `${groupKey}_${traj.name}`;
              allSolutionIds.add(solutionId);
            }
          });
        });
        setHiddenSolutions(allSolutionIds);
        
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [selectedFile]);

  // Process data when group is selected
  useEffect(() => {
    if (!experiment || !selectedGroup) return;

    setLoading(true);
    
    try {
      const groupData = experiment.data[selectedGroup as keyof typeof experiment.data] as TrajectoryGroup;
      
      // Set batch starting times
      if (groupData.batch_starting_time) {
        setBatchStartTimes(groupData.batch_starting_time);
      } else {
        setBatchStartTimes([]);
      }
      
      // Find reference trajectory and other trajectories
      const referenceTrajectory = groupData.trajectories.find(traj => traj.reference === true);
      const otherTrajectories = groupData.trajectories.filter(traj => traj.reference !== true);
      
      if (!referenceTrajectory || !referenceTrajectory.series) {
        setError("No reference trajectory found in selected group");
        setLoading(false);
        return;
      }
      
      const refSeries = referenceTrajectory.series;
      const timeArr = refSeries.time.time;
      
      // Create unified flat data containing reference + other trajectories
      const groupedByVar: GroupedLines = {};
      const flatData: FlatDataPoint[] = timeArr.map((t: number, i: number) => {
        const point: FlatDataPoint = { time: t };
        
        // 1. Process reference series data (clean keys for visualization compatibility)
        const processCoordinate = (coordSeries: any[], varName: string, timeIndex: number, prefix: string = '') => {
          coordSeries.forEach(coord => {
            const coordinateName = `coor_${coord.coordinate_number}`;
            const key = prefix ? `${prefix}.${coordinateName}.${varName}` : `${coordinateName}.${varName}`;
            
            if (timeIndex < coord.data.length) {
              point[key] = coord.data[timeIndex];
              
              // Group by variable type, then by coordinate
              if (!groupedByVar[varName]) groupedByVar[varName] = {};
              if (!groupedByVar[varName][coordinateName]) groupedByVar[varName][coordinateName] = [];
              if (!groupedByVar[varName][coordinateName].includes(key)) {
                groupedByVar[varName][coordinateName].push(key);
              }
            }
          });
        };
        
        // Process reference trajectory
        processCoordinate(refSeries.qpos.series, 'qpos', i);
        processCoordinate(refSeries.qvel.series, 'qvel', i);
        processCoordinate(refSeries.qacc.series, 'qacc', i);
        processCoordinate(refSeries.forces.series, 'forces', i);
        
        // 2. Process other trajectories (prefixed keys)
        otherTrajectories.forEach(traj => {
          if (!traj.series) return;
          
          const trajPrefix = traj.name.substring(0, 8); // Use first 8 chars as prefix
          const trajTime = traj.series.time.time;
          
          // Find closest time index for this trajectory
          let closestIndex = i;
          if (trajTime.length !== timeArr.length) {
            const targetTime = timeArr[i];
            closestIndex = trajTime.reduce((closest, time, idx) => {
              return Math.abs(time - targetTime) < Math.abs(trajTime[closest] - targetTime) ? idx : closest;
            }, 0);
          }
          
          // Process all coordinates with trajectory prefix
          processCoordinate(traj.series.qpos.series, 'qpos', closestIndex, trajPrefix);
          processCoordinate(traj.series.qvel.series, 'qvel', closestIndex, trajPrefix);
          processCoordinate(traj.series.qacc.series, 'qacc', closestIndex, trajPrefix);
          processCoordinate(traj.series.forces.series, 'forces', closestIndex, trajPrefix);
        });
        
        return point;
      });
      
      // Transform data and lines to use ranking numbers instead of UIDs
      const transformedData = transformDataWithRanking(flatData, rankingMap, hiddenSolutions);
      
      // Transform groupedLines to use ranking numbers
      const transformedGroupedLines: GroupedLines = {};
      Object.entries(groupedByVar).forEach(([varType, coordinateGroups]) => {
        transformedGroupedLines[varType] = {};
        Object.entries(coordinateGroups).forEach(([coordinateName, lines]) => {
          transformedGroupedLines[varType][coordinateName] = transformLinesWithRanking(lines, rankingMap, hiddenSolutions);
        });
      });
      
      setData(transformedData);
      setGroupedLines(transformedGroupedLines);
      setCurrentIdx(0);
      setLoading(false);
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  }, [experiment, selectedGroup, hiddenSolutions, rankingMap]);

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

  // Check if relative mode should be available (has non-reference lines)
  const hasNonReferenceLines = React.useMemo(() => {
    return Object.values(groupedLines).some(coordinateGroups =>
      Object.values(coordinateGroups).some(lines =>
        lines.some(line => {
          const parts = line.split('.');
          // Lines with ranking prefix (e.g., "1.coor_0.qpos") - first part should be a number
          return parts.length > 2 && !isNaN(parseInt(parts[0]));
        })
      )
    );
  }, [groupedLines]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Enhanced Sticky Header */}
      <header className="sticky top-0 z-50 bg-white shadow-lg border-b border-gray-200 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* App Title with Icon */}
            <div className="flex items-center space-x-3">
              <img src="logo.svg" alt="Uni-SINDy Logo" className="w-8 h-8" />
              <h1 className="text-xl font-bold text-gray-800 tracking-tight">
                Uni-SINDy Presentation Website
              </h1>
            </div>
            
            {/* Navigation Tabs */}
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setCurrentView('data')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  currentView === 'data'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Data Visualisation
              </button>
              <button
                onClick={() => setCurrentView('slides')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  currentView === 'slides'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Presentation Slides
              </button>
            </div>
          </div>
          
          {/* Enhanced Time Slider with Group Selection - Only show for data view */}
          {currentView === 'data' && data.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <TimeSlider
                      times={data.map((d) => Number(d.time))}
                      onChange={setCurrentIdx}
                    />
                  </div>
                  {/* Group Selection */}
                  <div className="flex items-center space-x-2 flex-shrink-0">
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
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      {currentView === 'slides' ? (
        <PresentationSlides />
      ) : (
      <div className="max-w-7xl mx-auto p-4">
        
        {/* File Explorer Section */}
        <div className="mb-6">
          <FileExplorer onFileSelect={handleFileSelect} selectedFile={selectedFile} />
        </div>

        {/* Generation Settings Section */}
        {generationParams !== null && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <GenerationSettings settings={generationParams} />
          </div>
        )}

        {/* Solution Control Table - Full Width Section */}
        {experiment && (
          <div className="mb-6">
            <SolutionControlTable 
              experiment={experiment}
              onSolutionToggle={handleSolutionToggle}
            />
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
              dataPoint={data[currentIdx]}
              positionRange={getPositionRange()}
              forceRange={getForceRange()}
              width={500}
              height={350}
            />
          </div>
        )}

        {/* Solution Analysis Tables */}
        {!loading && !error && selectedGroup && experiment && (
          <SolutionTables 
            experiment={experiment}
            selectedGroup={selectedGroup}
            hiddenSolutions={hiddenSolutions}
          />
        )}

        {/* Status */}
        {loading && <p className="text-center text-gray-600">Loading data...</p>}
        {error && <p className="text-center text-red-500">Error: {error}</p>}
        
        {/* Visualizations */}
        {!loading && !error && data.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">
                Data Visualization ({selectedGroup})
                {batchStartTimes.length > 0 && (
                  <span className="text-sm text-gray-500 ml-2">
                    - {batchStartTimes.length} batches
                  </span>
                )}
              </h2>
              <div className="flex items-center space-x-2">
                <span className={`text-sm ${hasNonReferenceLines ? 'text-gray-600' : 'text-gray-400'}`}>
                  Relative
                </span>
                <label className={`relative inline-flex items-center ${hasNonReferenceLines ? 'cursor-pointer' : 'cursor-not-allowed'}`}>
                  <input
                    type="checkbox"
                    checked={relativeMode}
                    onChange={(e) => hasNonReferenceLines && setRelativeMode(e.target.checked)}
                    disabled={!hasNonReferenceLines}
                    className="sr-only"
                  />
                  <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                    !hasNonReferenceLines 
                      ? 'bg-gray-100 border border-gray-300' 
                      : relativeMode 
                        ? 'bg-blue-600' 
                        : 'bg-gray-200'
                  }`}>
                    <div className={`w-5 h-5 rounded-full shadow transform transition-transform duration-200 ${
                      relativeMode && hasNonReferenceLines ? 'translate-x-5' : 'translate-x-0'
                    } mt-0.5 ml-0.5 ${
                      !hasNonReferenceLines ? 'bg-gray-300' : 'bg-white'
                    }`}></div>
                  </div>
                </label>
              </div>
            </div>
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
                          relative={relativeMode}
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
      )}
    </div>
  );
};

export default App;