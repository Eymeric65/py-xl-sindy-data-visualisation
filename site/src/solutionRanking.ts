// Utility for creating consistent solution rankings across components

export interface ExtraInfo {
  noise_level: number;
  optimization_function: string;
  regression_type: string;
  valid?: boolean;
  regression_time?: number;
  results?: {
    RMSE_acceleration?: number;
  };
}

export interface SolutionRanking {
  uid: string;
  rank: number;
  extraInfo: ExtraInfo;
}

export interface GroupData {
  data: {
    [seriesName: string]: {
      solution?: {
        [solutionType: string]: any;
      };
      reference?: boolean;
      extra_info?: ExtraInfo;
    };
  };
}

// Custom sorting function to rank solutions by Type, Optimizer, Noise
function rankSolutions(solutions: { uid: string; extraInfo: ExtraInfo }[]): SolutionRanking[] {
  return solutions
    .sort((a, b) => {
      // Primary sort: Regression type (alphabetical)
      if (a.extraInfo.regression_type !== b.extraInfo.regression_type) {
        return a.extraInfo.regression_type.localeCompare(b.extraInfo.regression_type);
      }
      
      // Secondary sort: Optimization function (alphabetical)
      if (a.extraInfo.optimization_function !== b.extraInfo.optimization_function) {
        return a.extraInfo.optimization_function.localeCompare(b.extraInfo.optimization_function);
      }
      
      // Tertiary sort: Noise level (ascending: 0.0, 0.1, 0.2, ...)
      return a.extraInfo.noise_level - b.extraInfo.noise_level;
    })
    .map((solution, index) => ({
      uid: solution.uid,
      rank: index + 1,
      extraInfo: solution.extraInfo
    }));
}

// Create ranking from groups data
export function createSolutionRanking(groups: { [groupName: string]: GroupData }): Map<string, SolutionRanking> {
  const solutions: { uid: string; extraInfo: ExtraInfo }[] = [];
  
  // Collect all solutions with their extra_info
  Object.entries(groups).forEach(([, groupData]) => {
    Object.entries(groupData.data).forEach(([seriesName, seriesData]) => {
      if (seriesData.solution && seriesData.extra_info && !seriesData.reference) {
        // Use first 8 characters of seriesName as UID (consistent with existing prefix logic)
        const uid = seriesName.substring(0, 8);
        solutions.push({
          uid: uid,
          extraInfo: seriesData.extra_info
        });
      }
    });
  });
  
  // Remove duplicates based on UID
  const uniqueSolutions = solutions.filter((solution, index, self) => 
    index === self.findIndex(s => s.uid === solution.uid)
  );
  
  // Rank the solutions
  const rankedSolutions = rankSolutions(uniqueSolutions);
  
  // Create a map for easy lookup
  const rankingMap = new Map<string, SolutionRanking>();
  rankedSolutions.forEach(solution => {
    rankingMap.set(solution.uid, solution);
  });
  
  return rankingMap;
}

// Get ranking number for a given UID
export function getSolutionRank(uid: string, rankingMap: Map<string, SolutionRanking>): number | null {
  const solution = rankingMap.get(uid);
  return solution ? solution.rank : null;
}

// Transform line keys to use ranking numbers instead of UIDs
export function transformLinesWithRanking(
  lines: string[], 
  rankingMap: Map<string, SolutionRanking>,
  hiddenSolutions?: Set<string>
): string[] {
  return lines
    .filter(line => {
      // Filter out hidden solutions
      if (hiddenSolutions) {
        const parts = line.split('.');
        if (parts.length > 2) {
          const uid = parts[0];
          // Check if this solution is hidden (need to find the solutionId format)
          // For now, we'll check by UID prefix
          for (const hiddenId of hiddenSolutions) {
            if (hiddenId.includes(uid)) {
              return false;
            }
          }
        }
      }
      return true;
    })
    .map(line => {
      const parts = line.split('.');
      if (parts.length > 2) {
        // This is a prefixed line (e.g., "abcd1234.coor_0.qpos")
        const uid = parts[0];
        const rank = getSolutionRank(uid, rankingMap);
        if (rank !== null) {
          // Keep the coordinate and variable info but use ranking number as prefix
          // This maintains data integrity while showing clean numbers in legend
          return `${rank}.${parts.slice(1).join('.')}`;
        }
      }
      return line;
    });
}

// Transform data keys to use ranking numbers instead of UIDs  
export function transformDataWithRanking(
  data: any[], 
  rankingMap: Map<string, SolutionRanking>,
  hiddenSolutions?: Set<string>
): any[] {
  return data.map(point => {
    const newPoint: any = {};
    
    Object.entries(point).forEach(([key, value]) => {
      const parts = key.split('.');
      if (parts.length > 2) {
        // This is a prefixed key (e.g., "abcd1234.coor_0.qpos")
        const uid = parts[0];
        
        // Check if this solution is hidden
        let isHidden = false;
        if (hiddenSolutions) {
          for (const hiddenId of hiddenSolutions) {
            if (hiddenId.includes(uid)) {
              isHidden = true;
              break;
            }
          }
        }
        
        if (!isHidden) {
          const rank = getSolutionRank(uid, rankingMap);
          if (rank !== null) {
            // Keep coordinate and variable info but use ranking number as prefix
            // This maintains data integrity for proper relative computation
            const newKey = `${rank}.${parts.slice(1).join('.')}`;
            newPoint[newKey] = value;
          } else {
            newPoint[key] = value;
          }
        }
        // Skip hidden solutions (don't add to newPoint)
      } else {
        // Keep non-prefixed keys as-is
        newPoint[key] = value;
      }
    });
    
    return newPoint;
  });
}