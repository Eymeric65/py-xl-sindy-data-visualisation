import React, { useState, useEffect } from 'react';

// Simple SVG icons to replace Heroicons
const ChevronDownIcon: React.FC<{ className: string }> = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

const ChevronRightIcon: React.FC<{ className: string }> = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

interface FileInfo {
  filename: string;
  forces_scale_vector: number[];
  experiment_folder: string;
  damping_coefficients: number[];
}

interface FilesManifest {
  files: FileInfo[];
}

interface FileExplorerProps {
  onFileSelect: (filename: string) => void;
  selectedFile?: string;
}

// Helper function to convert folder names to human-readable format
const formatExperimentName = (folderName: string): string => {
  switch (folderName) {
    case 'double_pendulum_pm':
      return 'Double Pendulum';
    case 'cart_pole':
      return 'Cart Pole';
    case 'cart_pole_double':
      return 'Double Pendulum Cart Pole';
    default:
      // Fallback: convert underscores to spaces and capitalize
      return folderName.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
  }
};

interface CollapsibleSectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  level?: number;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ 
  title, 
  isOpen, 
  onToggle, 
  children, 
  level = 0 
}) => {
  const paddingLeft = `${(level * 1.5) + 0.5}rem`;
  const bgColor = level === 0 ? 'bg-gray-50' : level === 1 ? 'bg-gray-25' : 'bg-white';
  
  return (
    <div className="border-b border-gray-200 last:border-b-0">
      <button
        onClick={onToggle}
        className={`w-full px-4 py-2 text-left flex items-center justify-between hover:bg-gray-100 transition-colors ${bgColor}`}
        style={{ paddingLeft }}
      >
        <span className={`font-medium ${level === 0 ? 'text-gray-800' : 'text-gray-700'}`}>
          {title}
        </span>
        {isOpen ? (
          <ChevronDownIcon className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronRightIcon className="h-4 w-4 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="border-l-2 border-gray-200 ml-4">
          {children}
        </div>
      )}
    </div>
  );
};

const ForceDot: React.FC<{ value: number }> = ({ value }) => {
  const isZero = Math.abs(value) < 1e-10;
  const color = isZero ? 'bg-red-500' : 'bg-green-500';
  
  return (
    <div className={`w-3 h-3 rounded-full ${color} mx-1`} />
  );
};

const ForcePattern: React.FC<{ forces: number[] }> = ({ forces }) => {
  return (
    <div className="flex items-center">
      {forces.map((force, index) => (
        <ForceDot key={index} value={force} />
      ))}
    </div>
  );
};

const FileExplorer: React.FC<FileExplorerProps> = ({ onFileSelect, selectedFile }) => {
  const [manifest, setManifest] = useState<FilesManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [userHasCollapsed, setUserHasCollapsed] = useState<boolean>(false);

  // Load the files manifest
  useEffect(() => {
    fetch('results/files.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load files manifest');
        return res.json();
      })
      .then((data: FilesManifest) => {
        setManifest(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const toggleSection = (sectionId: string) => {
    setOpenSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  // Auto-expand when a file is selected (only if user hasn't manually collapsed)
  useEffect(() => {
    if (selectedFile && !isExpanded && !userHasCollapsed) {
      setIsExpanded(true);
    }
  }, [selectedFile, userHasCollapsed]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">
          <h3 className="font-semibold mb-2">Error Loading Files</h3>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!manifest || !manifest.files) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">No files found</p>
      </div>
    );
  }

  // Group files by experiment folder, then by damping coefficients, then by forces
  const groupedFiles = manifest.files.reduce((acc, file) => {
    const expFolder = file.experiment_folder;
    const dampingKey = JSON.stringify(file.damping_coefficients);
    const forcesKey = JSON.stringify(file.forces_scale_vector);

    if (!acc[expFolder]) {
      acc[expFolder] = {};
    }
    if (!acc[expFolder][dampingKey]) {
      acc[expFolder][dampingKey] = {};
    }
    if (!acc[expFolder][dampingKey][forcesKey]) {
      acc[expFolder][dampingKey][forcesKey] = [];
    }
    
    acc[expFolder][dampingKey][forcesKey].push(file);
    return acc;
  }, {} as Record<string, Record<string, Record<string, FileInfo[]>>>);

  const formatDampingCoefficients = (coefficients: number[]): string => {
    return `Damping: [${coefficients.map(c => c.toFixed(1)).join(', ')}]`;
  };

  // Helper function to calculate damping magnitude for sorting
  const getDampingMagnitude = (dampingCoeffs: number[]): number => {
    return dampingCoeffs.reduce((sum, coeff) => sum + Math.abs(coeff), 0);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div 
        className="px-4 py-3 border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => {
          const newExpanded = !isExpanded;
          setIsExpanded(newExpanded);
          // Track if user manually collapsed to prevent auto-expand
          if (!newExpanded) {
            setUserHasCollapsed(true);
          }
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Experiment Files</h3>
            <p className="text-sm text-gray-600 mt-1">
              {manifest?.files ? `${manifest.files.length} files organized by experiment, damping, and forces` : 'Loading...'}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {selectedFile && manifest && (() => {
              const selectedFileInfo = manifest.files.find(f => f.filename === selectedFile);
              if (selectedFileInfo) {
                const humanName = formatExperimentName(selectedFileInfo.experiment_folder);
                const dampingStr = selectedFileInfo.damping_coefficients.map(c => c.toFixed(1)).join(', ');
                return (
                  <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded flex items-center space-x-2">
                    <span>Selected: {humanName} - Damping: [{dampingStr}]</span>
                    <span className="flex items-center space-x-1">
                      <span>Forces mode:</span>
                      <div className="flex items-center">
                        {selectedFileInfo.forces_scale_vector.map((force, index) => {
                          const isZero = Math.abs(force) < 1e-10;
                          const color = isZero ? 'bg-red-500' : 'bg-green-500';
                          return (
                            <div key={index} className={`w-2 h-2 rounded-full ${color} mx-0.5`} />
                          );
                        })}
                      </div>
                    </span>
                  </span>
                );
              }
              return null;
            })()}
            {isExpanded ? (
              <ChevronDownIcon className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronRightIcon className="h-5 w-5 text-gray-500" />
            )}
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className=" overflow-y-auto">
        {Object.entries(groupedFiles).map(([expFolder, dampingGroups]) => {
          const expSectionId = `exp-${expFolder}`;
          const isExpOpen = openSections.has(expSectionId);
          
          return (
            <CollapsibleSection
              key={expFolder}
              title={`${formatExperimentName(expFolder)} (${Object.values(dampingGroups).reduce((sum, forceGroups) => 
                sum + Object.values(forceGroups).reduce((s, files) => s + files.length, 0), 0)} files)`}
              isOpen={isExpOpen}
              onToggle={() => toggleSection(expSectionId)}
              level={0}
            >
              {Object.entries(dampingGroups)
                .sort(([dampingKeyA], [dampingKeyB]) => {
                  const dampingA = JSON.parse(dampingKeyA) as number[];
                  const dampingB = JSON.parse(dampingKeyB) as number[];
                  return getDampingMagnitude(dampingA) - getDampingMagnitude(dampingB);
                })
                .map(([dampingKey, forceGroups]) => {
                const dampingCoeffs = JSON.parse(dampingKey) as number[];
                const dampingSectionId = `${expSectionId}-damping-${dampingKey}`;
                const isDampingOpen = openSections.has(dampingSectionId);
                
                return (
                  <CollapsibleSection
                    key={dampingKey}
                    title={`${formatDampingCoefficients(dampingCoeffs)} (${Object.values(forceGroups).reduce((s, files) => s + files.length, 0)} files)`}
                    isOpen={isDampingOpen}
                    onToggle={() => toggleSection(dampingSectionId)}
                    level={1}
                  >
                    {Object.entries(forceGroups).map(([forcesKey, files]) => {
                      const forces = JSON.parse(forcesKey) as number[];
                      // Since there's only one file per force category, get the first (and only) file
                      const file = files[0];
                      const humanReadableName = formatExperimentName(file.experiment_folder);
                      const summaryName = `${humanReadableName} - Damping: [${file.damping_coefficients.map(c => c.toFixed(1)).join(', ')}]`;
                      
                      return (
                        <div key={forcesKey} className="border-b border-gray-100 last:border-b-0">
                          <button
                            onClick={() => onFileSelect(file.filename)}
                            className={`w-full px-4 py-2 bg-white hover:bg-gray-50 transition-colors ${
                              selectedFile === file.filename
                                ? 'bg-blue-50 border-l-4 border-blue-400'
                                : ''
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-gray-600">Forces mode:</span>
                                <ForcePattern forces={forces} />
                              </div>
                              <div className="flex-1 text-left">
                                <div className="text-sm font-medium text-gray-800">
                                  {summaryName}
                                </div>
                              </div>
                            </div>
                          </button>
                        </div>
                      );
                    })}
                  </CollapsibleSection>
                );
              })}
            </CollapsibleSection>
          );
        })}
        </div>
      )}
      
      {isExpanded && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span>Non-zero force</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 rounded-full bg-red-500"></div>
              <span>Zero force</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileExplorer;