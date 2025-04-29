import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, SkipForward, SkipBack } from 'lucide-react';
import useSound from 'use-sound';

interface MusicPlayerProps {
  tracks: string[];
}

const MusicPlayer: React.FC<MusicPlayerProps> = ({ tracks }) => {
  const [isMuted, setIsMuted] = useState(true);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [play, { stop }] = useSound(tracks[currentTrackIndex] || '', { 
    volume: 0.3,
    loop: true 
  });

  useEffect(() => {
    if (isMuted) {
      stop();
    } else {
      play();
    }
  }, [isMuted, currentTrackIndex, play, stop]);

  const nextTrack = () => {
    setCurrentTrackIndex((prev) => (prev + 1) % tracks.length);
  };

  const previousTrack = () => {
    setCurrentTrackIndex((prev) => (prev - 1 + tracks.length) % tracks.length);
  };

  if (tracks.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 flex items-center gap-2">
      {tracks.length > 1 && (
        <button
          onClick={previousTrack}
          className="w-10 h-10 bg-white bg-opacity-80 rounded-full shadow-lg flex items-center justify-center hover:bg-opacity-100 transition-all duration-300"
          title="השיר הקודם"
        >
          <SkipBack className="w-5 h-5 text-pink-500" />
        </button>
      )}
      
      <button
        onClick={() => setIsMuted(!isMuted)}
        className="w-12 h-12 bg-white bg-opacity-80 rounded-full shadow-lg flex items-center justify-center hover:bg-opacity-100 transition-all duration-300"
        title={isMuted ? 'הפעל מוזיקה' : 'השתק מוזיקה'}
      >
        {isMuted ? (
          <VolumeX className="w-6 h-6 text-pink-500" />
        ) : (
          <Volume2 className="w-6 h-6 text-pink-500" />
        )}
      </button>

      {tracks.length > 1 && (
        <button
          onClick={nextTrack}
          className="w-10 h-10 bg-white bg-opacity-80 rounded-full shadow-lg flex items-center justify-center hover:bg-opacity-100 transition-all duration-300"
          title="השיר הבא"
        >
          <SkipForward className="w-5 h-5 text-pink-500" />
        </button>
      )}
    </div>
  );
};

export default MusicPlayer