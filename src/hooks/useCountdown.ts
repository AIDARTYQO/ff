import { useState, useEffect } from 'react';
import { calculateTimeRemaining } from '../utils/dateUtils';
import { CountdownValues } from '../types';

export const useCountdown = (targetDate: Date | null): CountdownValues => {
  const [countdown, setCountdown] = useState<CountdownValues>({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  });

  useEffect(() => {
    if (!targetDate) {
      setCountdown({ days: 0, hours: 0, minutes: 0, seconds: 0 });
      return;
    }

    // Initial calculation
    setCountdown(calculateTimeRemaining(targetDate));

    // Update countdown every second
    const interval = setInterval(() => {
      const timeRemaining = calculateTimeRemaining(targetDate);
      setCountdown(timeRemaining);
      
      // Clear interval if countdown reaches zero
      if (
        timeRemaining.days === 0 &&
        timeRemaining.hours === 0 &&
        timeRemaining.minutes === 0 &&
        timeRemaining.seconds === 0
      ) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [targetDate]);

  return countdown;
};