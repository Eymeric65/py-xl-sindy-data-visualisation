import React from "react";

type GenerationSettingsProps = {
  settings: any;
};

const GenerationSettings: React.FC<GenerationSettingsProps> = ({ settings }) => {
  if (!settings) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Experiment Configuration</h2>
        <p className="text-gray-500">No generation settings available</p>
      </div>
    );
  }

  // Helper to format field names for display
  const formatFieldName = (key: string): string => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  // Helper to render array values nicely
  const renderArrayValue = (arr: any[]): React.ReactNode => {
    if (arr.length === 0) return <span className="text-gray-400 italic">Empty</span>;
    
    if (arr.length <= 4) {
      return (
        <div className="flex flex-wrap gap-1">
          {arr.map((item, index) => (
            <span key={index} className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              {item}
            </span>
          ))}
        </div>
      );
    }
    
    // For longer arrays, show first few + count
    return (
      <div className="flex flex-wrap gap-1">
        {arr.slice(0, 3).map((item, index) => (
          <span key={index} className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
            {item}
          </span>
        ))}
        <span className="inline-flex px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
          +{arr.length - 3} more
        </span>
      </div>
    );
  };

  // Helper to get appropriate styling based on value type
  const getValueStyling = (key: string, value: any) => {
    if (typeof value === 'number') {
      if (key.includes('time') || key.includes('sample')) {
        return 'text-green-700 font-semibold';
      }
      return 'text-blue-700 font-medium';
    }
    if (typeof value === 'string') {
      return 'text-purple-700 font-medium';
    }
    return 'text-gray-700';
  };

  // Organize settings into logical groups
  const settingGroups = [
    {
      title: 'Experiment Overview',
      icon: '🔬',
      fields: ['generation_type', 'experiment_folder', 'batch_number'],
    },
    {
      title: 'Time Configuration',
      icon: '⏱️',
      fields: ['max_time', 'validation_time', 'sample_number', 'max_validation_sample', 'visualisation_sample'],
    },
    {
      title: 'Force Parameters', 
      icon: '⚡',
      fields: ['forces_period', 'forces_period_shift', 'forces_scale_vector'],
    },
    {
      title: 'Initial Conditions',
      icon: '🎯',
      fields: ['initial_position', 'initial_condition_randomness', 'random_seed'],
    },
    {
      title: 'Physical Properties',
      icon: '🔧',
      fields: ['damping_coefficients'],
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Experiment Configuration</h2>
        <p className="text-sm text-gray-600 mt-1">
          Generation settings for the current simulation
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {settingGroups.map((group) => {
            const groupFields = group.fields.filter(field => settings.hasOwnProperty(field));
            if (groupFields.length === 0) return null;

            return (
              <div key={group.title} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">{group.icon}</span>
                  <h3 className="font-semibold text-gray-800">{group.title}</h3>
                </div>
                
                <div className="space-y-3">
                  {groupFields.map((field) => {
                    const value = settings[field];
                    const isArray = Array.isArray(value);
                    
                    return (
                      <div key={field} className="bg-white rounded p-3 border border-gray-200">
                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                          {formatFieldName(field)}
                        </div>
                        <div className="text-sm">
                          {isArray ? (
                            renderArrayValue(value)
                          ) : (
                            <span className={getValueStyling(field, value)}>
                              {typeof value === 'string' && value.includes('/') ? (
                                <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs">
                                  {field === 'experiment_folder' ? value.split('/').pop() : value}
                                </span>
                              ) : (
                                value?.toString() || 'N/A'
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Additional fields that don't fit in groups */}
        {Object.entries(settings).some(([key]) => 
          !settingGroups.some(group => group.fields.includes(key))
        ) && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <span>📋</span>
              Additional Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(settings)
                .filter(([key]) => !settingGroups.some(group => group.fields.includes(key)))
                .map(([key, value]) => (
                  <div key={key} className="bg-gray-50 rounded p-3 border border-gray-100">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                      {formatFieldName(key)}
                    </div>
                    <div className={`text-sm ${getValueStyling(key, value)}`}>
                      {Array.isArray(value) ? renderArrayValue(value) : (
                        typeof value === 'string' && value.includes('/') && key === 'experiment_folder' ? 
                          <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs">
                            {value.split('/').pop()}
                          </span> :
                          (value?.toString() || 'N/A')
                      )}
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

export default GenerationSettings;