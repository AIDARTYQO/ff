import React, { useState, useEffect } from 'react';
import CountdownDisplay from './CountdownDisplay';
import WeddingDetails from './WeddingDetails';
import ThemeSelector from './ThemeSelector';
import PhotoGallery from './PhotoGallery';
import MusicPlayer from './MusicPlayer';
import { useCountdown } from '../hooks/useCountdown';
import { WeddingDetails as WeddingDetailsType, ThemeOption } from '../types';
import { loadWeddingDetails, saveWeddingDetails, formatDate } from '../utils/dateUtils';

const themes: ThemeOption[] = [
  { 
    id: 'romantic', 
    name: 'רומנטי', 
    bgClass: 'bg-gradient-to-br from-pink-200 to-rose-400',
    textClass: 'text-pink-900' 
  },
  { 
    id: 'elegant', 
    name: 'אלגנטי', 
    bgClass: 'bg-gradient-to-br from-gray-200 to-gray-500',
    textClass: 'text-gray-900' 
  },
  { 
    id: 'garden', 
    name: 'גן', 
    bgClass: 'bg-gradient-to-br from-green-200 to-emerald-400',
    textClass: 'text-emerald-900' 
  },
  { 
    id: 'golden', 
    name: 'זהב', 
    bgClass: 'bg-gradient-to-br from-amber-200 to-amber-500',
    textClass: 'text-amber-900' 
  },
];

const WeddingCountdown: React.FC = () => {
  const [weddingDetails, setWeddingDetails] = useState<WeddingDetailsType>({
    coupleName: '',
    weddingDate: null,
    venue: '',
    message: '',
    photos: [],
    music: []
  });
  
  const [selectedTheme, setSelectedTheme] = useState<string>('romantic');
  
  useEffect(() => {
    const savedDetails = loadWeddingDetails();
    if (savedDetails) {
      setWeddingDetails(savedDetails);
    }
    
    const savedTheme = localStorage.getItem('weddingTheme');
    if (savedTheme) {
      setSelectedTheme(savedTheme);
    }
  }, []);
  
  const handleThemeChange = (themeId: string) => {
    setSelectedTheme(themeId);
    localStorage.setItem('weddingTheme', themeId);
  };
  
  const updateWeddingDetails = (details: WeddingDetailsType) => {
    setWeddingDetails(details);
  };
  
  const countdown = useCountdown(weddingDetails.weddingDate);
  const currentTheme = themes.find(t => t.id === selectedTheme) || themes[0];
  const weddingHasPassed = weddingDetails.weddingDate && 
    new Date().getTime() > weddingDetails.weddingDate.getTime();
  
  return (
    <div className={`min-h-screen flex flex-col items-center justify-center p-6 ${currentTheme.bgClass} transition-all duration-700`}>
      <ThemeSelector 
        themes={themes}
        selectedTheme={selectedTheme}
        onSelectTheme={handleThemeChange}
      />
      
      <div className="w-full max-w-4xl mx-auto text-center" dir="rtl">
        {weddingDetails.weddingDate && (
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6 text-center">
            {weddingHasPassed ? (
              <span className={`${currentTheme.textClass}`}>
                {weddingDetails.coupleName} התחתנו!
              </span>
            ) : (
              <>
                <span className={`${currentTheme.textClass}`}>
                  {weddingDetails.coupleName}
                </span>
                <br />
                <span className="text-2xl md:text-3xl mt-2 block font-medium">
                  מתחתנים בעוד:
                </span>
              </>
            )}
          </h1>
        )}
        
        {weddingDetails.photos && weddingDetails.photos.length > 0 && (
          <PhotoGallery 
            photos={weddingDetails.photos}
            className="w-full max-w-2xl mx-auto mb-8 aspect-[3/2]"
          />
        )}
        
        {weddingDetails.weddingDate && !weddingHasPassed && (
          <CountdownDisplay 
            countdown={countdown} 
            className="mb-8"
          />
        )}
        
        {weddingDetails.weddingDate && (
          <div className="mb-8 text-xl">
            <span className="font-medium">
              {weddingHasPassed ? 'החתונה התקיימה ב:' : 'תאריך החתונה:'}
            </span>
            <span className="mr-2">
              {formatDate(weddingDetails.weddingDate)}
            </span>
          </div>
        )}
        
        <WeddingDetails 
          details={weddingDetails}
          onUpdate={updateWeddingDetails}
          className="max-w-md mx-auto"
        />
      </div>
      
      {weddingHasPassed && (
        <div className="mt-8 text-center animate-pulse">
          <p className="text-2xl font-bold">❤️ מזל טוב! ❤️</p>
        </div>
      )}

      {weddingDetails.music && weddingDetails.music.length > 0 && (
        <MusicPlayer tracks={weddingDetails.music} />
      )}
    </div>
  );
};

export default WeddingCountdown