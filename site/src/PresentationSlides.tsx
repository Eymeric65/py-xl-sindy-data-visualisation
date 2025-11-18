import React from 'react';

const PresentationSlides: React.FC = () => {
  return (
    <div className="w-full h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-7xl" style={{ position: 'relative', paddingBottom: '56.25%' }}>
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
  );
};

export default PresentationSlides;
