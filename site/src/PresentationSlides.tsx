import React from 'react';

const PresentationSlides: React.FC = () => {
  return (
    <div className="w-full bg-gray-900 flex flex-col items-center p-8 min-h-screen">
      {/* Iframe container with proper aspect ratio and shadow for floating effect */}
      <div className="w-full max-w-6xl my-auto">
        <div className="w-full shadow-2xl rounded-lg overflow-hidden" style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
          <iframe
            style={{
              width: '100%',
              height: '100%',
              position: 'absolute',
              left: '0px',
              top: '0px',
            }}
            frameBorder="0"
            width="100%"
            height="100%"
            allowFullScreen
            allow="autoplay"
            src="slides.html"
            title="Presentation Slides"
          />
        </div>
      </div>
      
      {/* Keyboard shortcuts tooltip */}
      <div className="w-full max-w-6xl mt-6 bg-gray-800 rounded-lg p-4 border border-gray-700 flex-shrink-0">
        <h3 className="text-white text-lg font-semibold mb-3">Keyboard Shortcuts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-start gap-3">
            <kbd className="bg-gray-700 text-white px-2 py-1 rounded text-sm font-mono min-w-[2rem] text-center">S</kbd>
            <div>
              <span className="text-white font-medium">Speaker View</span>
              <p className="text-gray-400 text-sm">Opens a separate window displaying speaker notes, a timer, and a preview of the upcoming slide.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <kbd className="bg-gray-700 text-white px-2 py-1 rounded text-sm font-mono min-w-[2rem] text-center">F</kbd>
            <div>
              <span className="text-white font-medium">Fullscreen</span>
              <p className="text-gray-400 text-sm">Toggles fullscreen mode for the presentation. Press Esc to exit fullscreen.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <kbd className="bg-gray-700 text-white px-2 py-1 rounded text-sm font-mono min-w-[2rem] text-center">Esc</kbd>
            <div>
              <span className="text-white font-medium">Overview Mode</span>
              <p className="text-gray-400 text-sm">Displays an overview of all slides, allowing for easy navigation.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <kbd className="bg-gray-700 text-white px-2 py-1 rounded text-sm font-mono min-w-[2rem] text-center">B / .</kbd>
            <div>
              <span className="text-white font-medium">Blackout</span>
              <p className="text-gray-400 text-sm">Toggles a black screen, useful for focusing audience attention or taking a break.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PresentationSlides;
