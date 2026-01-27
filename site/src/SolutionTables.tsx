import React, { useState, useMemo } from "react";
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import { createSolutionRanking } from './solutionRanking';
import type { SolutionRanking, GroupData as RankingGroupData } from './solutionRanking';
import type { Experiment, TrajectoryGroup } from './types';

type SolutionData = {
  vector: number[];
  label: string[];
  extraInfo?: ExtraInfo;
};

type ExtraInfo = {
  noise_level: number;
  optimization_function: string;
  regression_type: string;
  valid?: boolean;
  regression_time?: number;
  results?: {
    RMSE_acceleration?: number;
  };
};

type SolutionTablesProps = {
  experiment: Experiment;
  selectedGroup: string;
  hiddenSolutions?: Set<string>;
};

// Component to render solution information in a styled table format
const SolutionInfoCard: React.FC<{ extraInfo: ExtraInfo; seriesName: string; ranking?: SolutionRanking }> = ({ extraInfo, seriesName, ranking }) => {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 min-w-0">
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-semibold text-gray-700 truncate" title={seriesName}>
          Solution Info
        </div>
        {ranking && (
          <div className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full ml-2">
            #{ranking.rank}
          </div>
        )}
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600">Type:</span>
          <span className="font-medium text-blue-700 capitalize">{extraInfo.regression_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Noise:</span>
          <span className="font-medium text-green-700">{extraInfo.noise_level}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Optimizer:</span>
          <span className="font-medium text-purple-700 truncate" title={extraInfo.optimization_function}>
            {extraInfo.optimization_function.replace('_', ' ')}
          </span>
        </div>
        {extraInfo.valid !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-600">Valid:</span>
            <span className={`font-medium ${extraInfo.valid ? 'text-green-600' : 'text-red-600'}`}>
              {extraInfo.valid ? '✓' : '✗'}
            </span>
          </div>
        )}
        {extraInfo.results?.RMSE_acceleration !== undefined && extraInfo.results.RMSE_acceleration !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">RMSE:</span>
            <span className="font-medium text-orange-700">
              {extraInfo.results.RMSE_acceleration.toFixed(3)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

const SolutionTables: React.FC<SolutionTablesProps> = ({ experiment, selectedGroup, hiddenSolutions }) => {
  
  const [showValues, setShowValues] = useState(true);
  const [collapseZeros, setCollapseZeros] = useState(true);
  
  // Create ranking map for consistent solution numbering
  const rankingMap = useMemo(() => {
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
  
  // Helper function to safely format numbers
  const formatValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    if (typeof value === 'number') {
      return value.toFixed(6);
    }
    if (typeof value === 'string') {
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return numValue.toFixed(6);
      }
    }
    return String(value);
  };

  // Helper function to render LaTeX labels
  const renderLatexLabel = (label: string): React.ReactNode => {
    try {
      // Check if the label contains LaTeX (starts and ends with $$)
      if (label.startsWith('$$') && label.endsWith('$$')) {
        const latexContent = label.slice(2, -2); // Remove $$ wrapper
        return <BlockMath math={latexContent} />;
      }
      // Check for inline math (single $ wrapper)
      if (label.startsWith('$') && label.endsWith('$') && label.length > 2) {
        const latexContent = label.slice(1, -1); // Remove $ wrapper
        return <InlineMath math={latexContent} />;
      }
      // Return plain text if no LaTeX detected
      return label;
    } catch (error) {
      // Fallback to plain text if LaTeX rendering fails
      console.warn('LaTeX rendering failed for:', label, error);
      return label;
    }
  };

  // Helper function to render cell content based on toggle
  const renderCellContent = (value: any, isReference: boolean): React.ReactNode => {
    if (showValues) {
      return formatValue(value);
    } else {
      // Circle mode
      const numValue = typeof value === 'number' ? value : parseFloat(value);
      if (isNaN(numValue) || numValue === 0) {
        return ''; // Blank for zero or non-numeric values
      }
      return isReference ? '🟢' : '🔴'; // Green circle for reference, red for others
    }
  };

  // Helper function to check if all values in a row are zero
  const isRowAllZeros = (referenceValue: any, otherValues: any[]): boolean => {
    const refNum = typeof referenceValue === 'number' ? referenceValue : parseFloat(referenceValue);
    const refIsZero = isNaN(refNum) || refNum === 0;
    
    const allOthersZero = otherValues.every(value => {
      const num = typeof value === 'number' ? value : parseFloat(value);
      return isNaN(num) || num === 0;
    });
    
    return refIsZero && allOthersZero;
  };

  // Extract all solution types and collect solution data from experiment
  const solutionTypes = new Set<string>();
  const solutionData: { [solutionType: string]: { [groupName: string]: { [trajectoryName: string]: SolutionData } } } = {};

  // Get the selected group
  const groupData = experiment.data[selectedGroup as keyof typeof experiment.data] as TrajectoryGroup;
  
  // Collect all solution data organized by solution type
  groupData.trajectories.forEach(traj => {
    if (traj.solutions && traj.regression_result) {
      const regressionResult = traj.regression_result; // Capture for null safety
      traj.solutions.forEach(sol => {
        const solutionType = sol.mode_solution;
        solutionTypes.add(solutionType);
        
        if (!solutionData[solutionType]) {
          solutionData[solutionType] = {};
        }
        if (!solutionData[solutionType][selectedGroup]) {
          solutionData[solutionType][selectedGroup] = {};
        }
        
        // Store solution info with extra_info from regression_result
        solutionData[solutionType][selectedGroup][traj.name] = {
          vector: sol.solution_vector,
          label: sol.solution_label,
          extraInfo: {
            noise_level: regressionResult.regression_parameters.noise_level,
            optimization_function: regressionResult.regression_parameters.optimization_function,
            regression_type: regressionResult.regression_parameters.regression_type,
            valid: regressionResult.valid,
            regression_time: regressionResult.regression_time ?? undefined,
            results: {
              RMSE_acceleration: regressionResult.RMSE_acceleration ?? undefined
            }
          }
        };
      });
    }
  });

  // Find reference data (trajectory with reference: true)
  const findReferenceData = (solutionType: string) => {
    const refTraj = groupData.trajectories.find(traj => traj.reference === true);
    if (refTraj && refTraj.solutions) {
      const refSolution = refTraj.solutions.find(sol => sol.mode_solution === solutionType);
      if (refSolution) {
        return {
          groupName: selectedGroup,
          seriesName: refTraj.name,
          data: {
            vector: refSolution.solution_vector,
            label: refSolution.solution_label
          }
        };
      }
    }
    return null;
  };

  if (solutionTypes.size === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Solution Analysis</h2>
        <p className="text-gray-500">No solution data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Solution Analysis</h2>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Values</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={showValues}
                onChange={(e) => setShowValues(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                showValues ? 'bg-blue-600' : 'bg-gray-200'
              }`}>
                <div className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-200 ${
                  showValues ? 'translate-x-5' : 'translate-x-0'
                } mt-0.5 ml-0.5`}></div>
              </div>
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Collapse</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={collapseZeros}
                onChange={(e) => setCollapseZeros(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                collapseZeros ? 'bg-blue-600' : 'bg-gray-200'
              }`}>
                <div className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-200 ${
                  collapseZeros ? 'translate-x-5' : 'translate-x-0'
                } mt-0.5 ml-0.5`}></div>
              </div>
            </label>
          </div>
        </div>
      </div>
      
      <div className="space-y-6">
        {Array.from(solutionTypes).map((solutionType) => {
          const referenceData = findReferenceData(solutionType);
          
          if (!referenceData) {
            return null; // Skip if no reference data found
          }

          const { label: labels, vector: referenceVector } = referenceData.data;
          
          // Get all other series for this solution type
          const otherSeries: { groupName: string; seriesName: string; vector: number[]; extraInfo?: ExtraInfo; ranking?: SolutionRanking }[] = [];
          
          Object.entries(solutionData[solutionType]).forEach(([groupName, groupSeries]) => {
            Object.entries(groupSeries).forEach(([seriesName, seriesData]) => {
              // Skip the reference series
              if (groupName === referenceData.groupName && seriesName === referenceData.seriesName) {
                return;
              }
              
              // Skip hidden solutions
              const solutionId = `${groupName}_${seriesName}`;
              if (hiddenSolutions && hiddenSolutions.has(solutionId)) {
                return;
              }
              
              const uid = seriesName.substring(0, 8);
              const ranking = rankingMap.get(uid);
              otherSeries.push({
                groupName,
                seriesName,
                vector: seriesData.vector,
                extraInfo: seriesData.extraInfo,
                ranking: ranking
              });
            });
          });

          // Sort by ranking number first, then by groupName for consistent ordering
          otherSeries.sort((a, b) => {
            // Primary sort: by ranking number (ascending)
            if (a.ranking && b.ranking && a.ranking.rank !== b.ranking.rank) {
              return a.ranking.rank - b.ranking.rank;
            }
            
            // Secondary sort: by group name
            if (a.groupName !== b.groupName) {
              return a.groupName.localeCompare(b.groupName);
            }
            
            // Tertiary sort: by series name
            return a.seriesName.localeCompare(b.seriesName);
          });

          return (
            <div key={solutionType} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-800 capitalize">
                  {solutionType} Solutions
                  <span className="ml-2 text-sm text-gray-600 font-normal">
                    ({labels.length} parameters)
                  </span>
                </h3>
              </div>
              
              <div className="overflow-x-auto relative">
                <table className="min-w-full divide-y divide-gray-200 table-fixed">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="sticky left-0 z-30 bg-gray-50 px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48 min-w-48 max-w-48" style={{boxShadow: '2px 0 4px rgba(0,0,0,0.1)'}}>
                        Parameter
                      </th>
                      <th className="sticky left-48 z-30 bg-gray-50 px-4 py-2 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-40 min-w-40 max-w-40" style={{boxShadow: '2px 0 4px rgba(0,0,0,0.1)'}}>
                        {referenceData.seriesName}
                      </th>
                      {otherSeries.map((series, idx) => (
                        <th key={idx} className="px-2 py-2 text-left w-48 min-w-48">
                          {series.extraInfo ? (
                            <SolutionInfoCard 
                              extraInfo={series.extraInfo} 
                              seriesName={series.seriesName} 
                              ranking={series.ranking}
                            />
                          ) : (
                            <div className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                              {series.seriesName}
                            </div>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {labels.map((label, rowIdx) => {
                      // Check if this row should be collapsed
                      const otherValues = otherSeries.map(series => series.vector[rowIdx]);
                      const shouldCollapse = collapseZeros && isRowAllZeros(referenceVector[rowIdx], otherValues);
                      
                      if (shouldCollapse) {
                        return null; // Don't render this row
                      }
                      
                      return (
                        <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className={`sticky left-0 z-30 px-4 py-2 text-sm font-medium text-gray-900 w-48 min-w-48 max-w-48 overflow-hidden text-ellipsis ${rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`} style={{boxShadow: '2px 0 4px rgba(0,0,0,0.1)'}}>
                            <div className="truncate">{renderLatexLabel(label)}</div>
                          </td>
                          <td className={`sticky left-48 z-30 px-4 py-2 text-sm text-gray-700 font-mono w-40 min-w-40 max-w-40 overflow-hidden text-ellipsis ${rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`} style={{boxShadow: '2px 0 4px rgba(0,0,0,0.1)'}}>
                            <div className="truncate">{renderCellContent(referenceVector[rowIdx], true)}</div>
                          </td>
                          {otherSeries.map((series, colIdx) => (
                            <td key={colIdx} className="px-2 py-2 text-sm text-gray-700 font-mono w-48 min-w-48 overflow-hidden text-ellipsis text-center">
                              <div className="truncate">{renderCellContent(series.vector[rowIdx], false)}</div>
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SolutionTables;