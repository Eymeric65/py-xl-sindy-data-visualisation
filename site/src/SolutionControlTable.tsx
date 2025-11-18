import React, { useState, useMemo } from "react";
import { createSolutionRanking } from './solutionRanking';
import type { SolutionRanking, GroupData as RankingGroupData, ExtraInfo } from './solutionRanking';

interface SolutionControlTableProps {
  groups: {
    [groupName: string]: {
      data: {
        [seriesName: string]: {
          solution?: {
            [solutionType: string]: any;
          };
          reference?: boolean;
          extra_info?: ExtraInfo;
        };
      };
    };
  };
  onSolutionToggle?: (solutionId: string, isVisible: boolean) => void;
}

type SortField = 'rank' | 'solution_type' | 'regression_type' | 'optimization_function' | 'noise_level' | 'valid' | 'rmse';
type SortDirection = 'asc' | 'desc';

interface TableSolution extends SolutionRanking {
  id: string; // Full series name for identification
  groupName: string;
  isVisible: boolean;
  solutionType: string; // The parent key of extra_info (e.g., "linear", "nonlinear")
}

const SolutionControlTable: React.FC<SolutionControlTableProps> = ({ groups, onSolutionToggle }) => {
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [visibilityMap, setVisibilityMap] = useState<Map<string, boolean>>(new Map());

  // Create ranking and collect all solutions
  const allSolutions = useMemo(() => {
    const rankingMap = createSolutionRanking(groups as { [groupName: string]: RankingGroupData });
    const solutions: TableSolution[] = [];

    Object.entries(groups).forEach(([groupName, groupData]) => {
      Object.entries(groupData.data).forEach(([seriesName, seriesData]) => {
        if (seriesData.solution && seriesData.extra_info && !seriesData.reference) {
          const uid = seriesName.substring(0, 8);
          const ranking = rankingMap.get(uid);
          
          // Extract solution type (first key in solution object)
          const solutionType = Object.keys(seriesData.solution)[0] || 'unknown';
          
          if (ranking) {
            const solutionId = `${groupName}_${seriesName}`;
            solutions.push({
              ...ranking,
              id: solutionId,
              groupName: groupName,
              solutionType: solutionType,
              isVisible: visibilityMap.get(solutionId) ?? false
            });
          }
        }
      });
    });

    return solutions;
  }, [groups, visibilityMap]);

  // Sort solutions based on current sort field and direction
  const sortedSolutions = useMemo(() => {
    return [...allSolutions].sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'rank':
          comparison = a.rank - b.rank;
          break;
        case 'solution_type':
          comparison = a.solutionType.localeCompare(b.solutionType);
          break;
        case 'regression_type':
          comparison = a.extraInfo.regression_type.localeCompare(b.extraInfo.regression_type);
          break;
        case 'optimization_function':
          comparison = a.extraInfo.optimization_function.localeCompare(b.extraInfo.optimization_function);
          break;
        case 'noise_level':
          comparison = a.extraInfo.noise_level - b.extraInfo.noise_level;
          break;
        case 'valid':
          const aValid = a.extraInfo.valid ?? true;
          const bValid = b.extraInfo.valid ?? true;
          comparison = Number(aValid) - Number(bValid);
          break;
        case 'rmse':
          const aRmse = a.extraInfo.results?.RMSE_acceleration ?? Infinity;
          const bRmse = b.extraInfo.results?.RMSE_acceleration ?? Infinity;
          comparison = aRmse - bRmse;
          break;
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [allSolutions, sortField, sortDirection]);

  // Handle column header click for sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Handle solution visibility toggle
  const handleToggle = (solution: TableSolution) => {
    const newVisibility = !solution.isVisible;
    setVisibilityMap(prev => new Map(prev).set(solution.id, newVisibility));
    onSolutionToggle?.(solution.id, newVisibility);
  };

  // Handle clicking on values to toggle visibility of matching solutions
  const handleValueClick = (field: SortField, value: any) => {
    // Find all solutions with matching value in this field
    const matchingSolutions = sortedSolutions.filter(solution => {
      switch (field) {
        case 'rank':
          return solution.rank === value;
        case 'solution_type':
          return solution.solutionType === value;
        case 'regression_type':
          return solution.extraInfo.regression_type === value;
        case 'optimization_function':
          return solution.extraInfo.optimization_function === value;
        case 'noise_level':
          return solution.extraInfo.noise_level === value;
        case 'valid':
          return (solution.extraInfo.valid ?? true) === value;
        case 'rmse':
          return (solution.extraInfo.results?.RMSE_acceleration ?? Infinity) === value;
        default:
          return false;
      }
    });

    // Check if any matching solution is currently visible
    const anyVisible = matchingSolutions.some(sol => sol.isVisible);
    
    // Toggle all matching solutions (if any are visible, hide all; if none visible, show all)
    const newVisibility = !anyVisible;
    
    const newVisibilityMap = new Map(visibilityMap);
    matchingSolutions.forEach(solution => {
      newVisibilityMap.set(solution.id, newVisibility);
      onSolutionToggle?.(solution.id, newVisibility);
    });
    
    setVisibilityMap(newVisibilityMap);
  };

  // Handle bulk operations
  const handleSelectAll = () => {
    const newVisibilityMap = new Map(visibilityMap);
    sortedSolutions.forEach(solution => {
      newVisibilityMap.set(solution.id, true);
      onSolutionToggle?.(solution.id, true);
    });
    setVisibilityMap(newVisibilityMap);
  };

  const handleDeselectAll = () => {
    const newVisibilityMap = new Map(visibilityMap);
    sortedSolutions.forEach(solution => {
      newVisibilityMap.set(solution.id, false);
      onSolutionToggle?.(solution.id, false);
    });
    setVisibilityMap(newVisibilityMap);
  };

  // Render sort indicator
  const SortIndicator: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) return <span className="text-gray-300">⇅</span>;
    return sortDirection === 'asc' ? <span className="text-blue-600">↑</span> : <span className="text-blue-600">↓</span>;
  };

  const visibleCount = sortedSolutions.filter(s => s.isVisible).length;
  const totalCount = sortedSolutions.length;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Solution Control Center</h2>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-sm text-gray-600">
                {visibleCount} of {totalCount} solutions visible
              </p>
              <p className="text-xs text-red-600">
                ⚠️ Toggling all solutions at once may slow down your browser
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
            >
              Show All
            </button>
            <button
              onClick={handleDeselectAll}
              className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
            >
              Hide All
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Visible
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('rank')}
              >
                <div className="flex items-center gap-1">
                  Rank <SortIndicator field="rank" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('solution_type')}
              >
                <div className="flex items-center gap-1">
                  Solution Type <SortIndicator field="solution_type" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('regression_type')}
              >
                <div className="flex items-center gap-1">
                  Type <SortIndicator field="regression_type" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('optimization_function')}
              >
                <div className="flex items-center gap-1">
                  Optimizer <SortIndicator field="optimization_function" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('noise_level')}
              >
                <div className="flex items-center gap-1">
                  Noise Level <SortIndicator field="noise_level" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('valid')}
              >
                <div className="flex items-center gap-1">
                  Valid <SortIndicator field="valid" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('rmse')}
              >
                <div className="flex items-center gap-1">
                  RMSE <SortIndicator field="rmse" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Group
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedSolutions.map((solution) => (
              <tr 
                key={solution.id} 
                className={`hover:bg-gray-50 ${!solution.isVisible ? 'opacity-50 bg-gray-25' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={solution.isVisible}
                    onChange={() => handleToggle(solution)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div 
                      className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full cursor-pointer hover:bg-blue-700 transition-colors"
                      onClick={() => handleValueClick('rank', solution.rank)}
                      title="Click to toggle all solutions with this rank"
                    >
                      #{solution.rank}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full capitalize cursor-pointer hover:bg-indigo-200 transition-colors"
                    onClick={() => handleValueClick('solution_type', solution.solutionType)}
                    title="Click to toggle all solutions of this type"
                  >
                    {solution.solutionType}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full capitalize cursor-pointer hover:bg-blue-200 transition-colors"
                    onClick={() => handleValueClick('regression_type', solution.extraInfo.regression_type)}
                    title="Click to toggle all solutions with this regression type"
                  >
                    {solution.extraInfo.regression_type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full cursor-pointer hover:bg-purple-200 transition-colors"
                    onClick={() => handleValueClick('optimization_function', solution.extraInfo.optimization_function)}
                    title="Click to toggle all solutions with this optimizer"
                  >
                    {solution.extraInfo.optimization_function.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span 
                    className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full cursor-pointer hover:bg-green-200 transition-colors"
                    onClick={() => handleValueClick('noise_level', solution.extraInfo.noise_level)}
                    title="Click to toggle all solutions with this noise level"
                  >
                    {solution.extraInfo.noise_level}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {solution.extraInfo.valid !== undefined ? (
                    <span 
                      className={`text-sm cursor-pointer hover:opacity-70 transition-opacity ${
                        solution.extraInfo.valid ? 'text-green-600' : 'text-red-600'
                      }`}
                      onClick={() => handleValueClick('valid', solution.extraInfo.valid)}
                      title="Click to toggle all solutions with this validation status"
                    >
                      {solution.extraInfo.valid ? '✓' : '✗'}
                    </span>
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {solution.extraInfo.results?.RMSE_acceleration !== undefined ? (
                    <span 
                      className="text-sm font-mono text-gray-900 cursor-pointer hover:text-blue-600 transition-colors"
                      onClick={() => handleValueClick('rmse', solution.extraInfo.results!.RMSE_acceleration)}
                      title="Click to toggle all solutions with this RMSE value"
                    >
                      {solution.extraInfo.results.RMSE_acceleration.toFixed(4)}
                    </span>
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600">
                    {solution.groupName}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {sortedSolutions.length === 0 && (
        <div className="px-6 py-8 text-center text-gray-500">
          <p>No solutions found</p>
        </div>
      )}
    </div>
  );
};

export default SolutionControlTable;