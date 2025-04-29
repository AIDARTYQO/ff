import React from 'react';
import { CountdownValues } from '../types';

interface CountdownDisplayProps {
  countdown: CountdownValues;
  className?: string;
}

const CountdownDisplay: React.FC<CountdownDisplayProps> = ({ countdown, className = '' }) => {
  return (
    <div className={`grid grid-cols-4 gap-2 sm:gap-4 md:gap-6 lg:gap-8 ${className}`}>
      <CountdownUnit value={countdown.days} label="ימים" />
      <CountdownUnit value={countdown.hours} label="שעות" />
      <CountdownUnit value={countdown.minutes} label="דקות" />
      <CountdownUnit value={countdown.seconds} label="שניות" />
    </div>
  );
};

interface CountdownUnitProps {
  value: number;
  label: string;
}

const CountdownUnit: React.FC<CountdownUnitProps> = ({ value, label }) => {
  return (
    <div className="flex flex-col items-center">
      <div className="bg-white bg-opacity-90 backdrop-blur-sm rounded-lg shadow-lg w-16 sm:w-20 md:w-28 lg:w-32 h-16 sm:h-20 md:h-28 lg:h-32 flex items-center justify-center transition-all duration-300 transform hover:scale-105">
        <span className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold transition-all duration-500">
          {value}
        </span>
      </div>
      <span className="mt-2 text-sm sm:text-base font-medium">{label}</span>
    </div>
  );
};

export default CountdownDisplay;