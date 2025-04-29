import React, { useState, useEffect } from 'react';

interface PhotoGalleryProps {
  photos: string[];
  className?: string;
}

const PhotoGallery: React.FC<PhotoGalleryProps> = ({ photos, className = '' }) => {
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);

  useEffect(() => {
    if (photos.length === 0) return;

    const interval = setInterval(() => {
      setCurrentPhotoIndex((prevIndex) => 
        prevIndex === photos.length - 1 ? 0 : prevIndex + 1
      );
    }, 5000);

    return () => clearInterval(interval);
  }, [photos]);

  if (photos.length === 0) return null;

  return (
    <div className={`relative overflow-hidden rounded-lg shadow-lg ${className}`}>
      {photos.map((photo, index) => (
        <div
          key={photo}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentPhotoIndex ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <img
            src={photo}
            alt={`תמונת אירוסין ${index + 1}`}
            className="w-full h-full object-cover"
          />
        </div>
      ))}
    </div>
  );
};

export default PhotoGallery;