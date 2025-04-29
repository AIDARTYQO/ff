import React from 'react';
import { Heart } from 'lucide-react';
import { ThemeOption } from '../types';

interface ThemeSelectorProps {
  themes: ThemeOption[];
  selectedTheme: string;
  onSelectTheme: (themeId: string) => void;
}

const ThemeSelector: React.FC<ThemeSelectorProps> = ({ 
  themes, 
  selectedTheme, 
  onSelectTheme 
}) => {
  return (
    <div className="absolute top-4 left-4 z-10">
      <div className="relative group">
        <button className="w-10 h-10 rounded-full bg-white bg-opacity-80 flex items-center justify-center shadow-md hover:bg-opacity-100 transition-all duration-300">
          <Heart size={20} className="text-pink-500" />
        </button>
        
        <div className="absolute left-0 top-12 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg shadow-lg p-3 transition-all duration-300 scale-0 origin-top-left group-hover:scale-100 min-w-48">
          <p className="text-sm font-medium mb-2 text-gray-700">בחר עיצוב:</p>
          <div className="grid grid-cols-2 gap-2">
            {themes.map((theme) => (
              <button
                key={theme.id}
                onClick={() => onSelectTheme(theme.id)}
                className={`w-full h-12 rounded-md transition-all duration-300 ${
                  selectedTheme === theme.id 
                    ? 'ring-2 ring-pink-500 scale-105' 
                    : 'hover:scale-105'
                } ${theme.bgClass}`}
                title={theme.name}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeSelector;