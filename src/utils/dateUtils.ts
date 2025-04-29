export const calculateTimeRemaining = (targetDate: Date | null): {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
} => {
  if (!targetDate) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 };
  }

  const currentTime = new Date().getTime();
  const targetTime = targetDate.getTime();
  const timeRemaining = targetTime - currentTime;

  // If the date has passed, return zeros
  if (timeRemaining <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 };
  }

  // Calculate time units
  const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
  const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);

  return { days, hours, minutes, seconds };
};

export const formatDate = (date: Date): string => {
  return date.toLocaleDateString('he-IL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const saveWeddingDetails = (details: any): void => {
  const detailsToSave = {
    ...details,
    weddingDate: details.weddingDate ? details.weddingDate.toISOString() : null,
  };
  localStorage.setItem('weddingDetails', JSON.stringify(detailsToSave));
};

export const loadWeddingDetails = (): any => {
  const savedDetails = localStorage.getItem('weddingDetails');
  if (!savedDetails) return null;
  
  const parsedDetails = JSON.parse(savedDetails);
  return {
    ...parsedDetails,
    weddingDate: parsedDetails.weddingDate ? new Date(parsedDetails.weddingDate) : null,
  };
};