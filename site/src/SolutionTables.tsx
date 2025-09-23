import React, { useState } from "react";
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';

type SolutionData = {
  vector: number[];
  label: string[];
};

type SeriesData = {
  solution?: {
    [solutionType: string]: SolutionData;
  };
  reference?: boolean;
};

type GroupData = {
  data: {
    [seriesName: string]: SeriesData;
  };
};

type SolutionTablesProps = {
  groups: {
    [groupName: string]: GroupData;
  };
};

const SolutionTables: React.FC<SolutionTablesProps> = ({ groups }) => {
  
  const [showValues, setShowValues] = useState(true);
  const [collapseZeros, setCollapseZeros] = useState(true);
  
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

  // Extract all solution types across all groups and series
  const solutionTypes = new Set<string>();
  const solutionData: { [solutionType: string]: { [groupName: string]: { [seriesName: string]: SolutionData } } } = {};

  // Collect all solution data organized by solution type
  Object.entries(groups).forEach(([groupName, groupData]) => {
    Object.entries(groupData.data).forEach(([seriesName, seriesData]) => {
      if (seriesData.solution) {
        Object.entries(seriesData.solution).forEach(([solutionType, solutionInfo]) => {
          solutionTypes.add(solutionType);
          
          if (!solutionData[solutionType]) {
            solutionData[solutionType] = {};
          }
          if (!solutionData[solutionType][groupName]) {
            solutionData[solutionType][groupName] = {};
          }
          solutionData[solutionType][groupName][seriesName] = solutionInfo;
        });
      }
    });
  });

  // Find reference data (series with reference: true)
  const findReferenceData = (solutionType: string) => {
    for (const [groupName, groupData] of Object.entries(groups)) {
      for (const [seriesName, seriesData] of Object.entries(groupData.data)) {
        if (seriesData.reference && seriesData.solution?.[solutionType]) {
          return {
            groupName,
            seriesName,
            data: seriesData.solution[solutionType]
          };
        }
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
          const otherSeries: { groupName: string; seriesName: string; vector: number[] }[] = [];
          
          Object.entries(solutionData[solutionType]).forEach(([groupName, groupSeries]) => {
            Object.entries(groupSeries).forEach(([seriesName, seriesData]) => {
              // Skip the reference series
              if (groupName === referenceData.groupName && seriesName === referenceData.seriesName) {
                return;
              }
              otherSeries.push({
                groupName,
                seriesName,
                vector: seriesData.vector
              });
            });
          });

          return (
            <div key={solutionType} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-800 capitalize">
                  {solutionType} Solutions
                </h3>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Parameter
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                        {referenceData.seriesName}
                      </th>
                      {otherSeries.map((series, idx) => (
                        <th key={idx} className="px-4 py-2 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                          {series.seriesName}
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
                          <td className="px-4 py-2 text-sm font-medium text-gray-900">
                            {renderLatexLabel(label)}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 font-mono">
                            {renderCellContent(referenceVector[rowIdx], true)}
                          </td>
                          {otherSeries.map((series, colIdx) => (
                            <td key={colIdx} className="px-4 py-2 text-sm text-gray-700 font-mono">
                              {renderCellContent(series.vector[rowIdx], false)}
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