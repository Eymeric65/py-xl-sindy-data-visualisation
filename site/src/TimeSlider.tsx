import React, { useState, useRef, useEffect } from "react";

interface TimeSliderProps {
  times: number[];
  onChange: (index: number) => void;
}

const TimeSlider: React.FC<TimeSliderProps> = ({ times, onChange }) => {
  const [current, setCurrent] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // Speed multiplier
  const intervalRef = useRef<number | null>(null);
  const lastTimestep = useRef<number |null>(0); // register last time timestamp
  const startCurrent = useRef<number|null>(null);
  const elapsedTime = useRef<number>(0);

  useEffect(() => {
    onChange(current);
  }, [current, onChange]);

  useEffect(() => {
    if (playing) {
      
      const update = (timestamp: DOMHighResTimeStamp):void =>  {

        if (startCurrent.current == null || lastTimestep.current == null){
          lastTimestep.current = timestamp;
          startCurrent.current = current;
        }

        const offset = (timestamp - lastTimestep.current) * speed;

        lastTimestep.current = timestamp;

        elapsedTime.current = elapsedTime.current + offset;


        setCurrent((prevIndex) => {
          let newIndex = prevIndex;
          
          // Check if we should advance based on data timing
          while (newIndex < times.length - 1) {
            const nextDataTime = times[newIndex + 1];
            const currentDataTime = times[newIndex];
            const timeToNext = (nextDataTime - currentDataTime)*1000;
            
            if (elapsedTime.current >= timeToNext) {
              elapsedTime.current = elapsedTime.current - timeToNext; // Subtract the time we "used"
              newIndex++;
            } else {
              break;
            }
          }
          
          if (newIndex >= times.length - 1) {
            setPlaying(false);
            return times.length - 1;
          }
          
          return newIndex;
        });
        
        if (playing) {
          intervalRef.current = requestAnimationFrame(update) as any;
        }
      };
      
      update(performance.now());
    } else if (intervalRef.current) {
      cancelAnimationFrame(intervalRef.current as any);
      startCurrent.current = null;
    }
    
    return () => {
      if (intervalRef.current) {
        cancelAnimationFrame(intervalRef.current as any);
        startCurrent.current = null;
      }
    };
  }, [playing, speed, times.length]);

  return (
    <div className="w-full flex flex-col items-center my-4">
      <div className="flex items-center gap-2 w-full max-w-3xl">
        <button
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={() => setPlaying((p) => !p)}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-600">Speed:</span>
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            className="text-xs px-1 py-0.5 border rounded"
          >
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
        </div>
        <input
          type="range"
          min={0}
          max={times.length - 1}
          value={current}
          onChange={(e) => setCurrent(Number(e.target.value))}
          className="flex-1 mx-2 accent-blue-500"
        />
        <span className="w-20 text-right text-sm text-gray-700 font-mono">
          {times[current]?.toFixed(3)} s
        </span>
      </div>
    </div>
  );
};

export default TimeSlider;
