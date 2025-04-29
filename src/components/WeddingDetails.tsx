import React, { useState, useEffect } from 'react';
import { WeddingDetails as WeddingDetailsType } from '../types';
import DatePicker from './DatePicker';
import { saveWeddingDetails } from '../utils/dateUtils';

interface WeddingDetailsProps {
  details: WeddingDetailsType;
  onUpdate: (details: WeddingDetailsType) => void;
  className?: string;
}

const WeddingDetails: React.FC<WeddingDetailsProps> = ({ 
  details, 
  onUpdate,
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(!details.weddingDate);
  const [formData, setFormData] = useState<WeddingDetailsType>(details);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleDateChange = (date: Date) => {
    setFormData((prev) => ({ ...prev, weddingDate: date }));
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newPhotos = Array.from(files).map(file => URL.createObjectURL(file));
    setFormData((prev) => ({
      ...prev,
      photos: [...(prev.photos || []), ...newPhotos]
    }));
  };

  const handleMusicUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newTracks = Array.from(files).map(file => URL.createObjectURL(file));
    setFormData((prev) => ({
      ...prev,
      music: [...(prev.music || []), ...newTracks]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdate(formData);
    saveWeddingDetails(formData);
    setIsEditing(false);
  };

  return (
    <div className={`bg-white bg-opacity-80 backdrop-blur-sm rounded-lg shadow-lg p-6 ${className}`}>
      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-4" dir="rtl">
          <div>
            <label htmlFor="coupleName" className="block mb-1 font-medium">
              שמות בני הזוג:
            </label>
            <input
              type="text"
              id="coupleName"
              name="coupleName"
              value={formData.coupleName}
              onChange={handleChange}
              placeholder="לדוגמא: דן ודנה"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
              required
            />
          </div>
          
          <DatePicker
            selectedDate={formData.weddingDate}
            onChange={handleDateChange}
          />
          
          <div>
            <label htmlFor="venue" className="block mb-1 font-medium">
              מקום האירוע:
            </label>
            <input
              type="text"
              id="venue"
              name="venue"
              value={formData.venue}
              onChange={handleChange}
              placeholder="שם אולם/גן האירועים"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
            />
          </div>
          
          <div>
            <label htmlFor="message" className="block mb-1 font-medium">
              הודעה אישית:
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              placeholder="הוסף הודעה אישית (לא חובה)"
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="photos" className="block mb-1 font-medium">
              תמונות אירוסין:
            </label>
            <input
              type="file"
              id="photos"
              name="photos"
              accept="image/*"
              multiple
              onChange={handlePhotoUpload}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
            />
          </div>

          <div>
            <label htmlFor="music" className="block mb-1 font-medium">
              שירים לרקע:
            </label>
            <input
              type="file"
              id="music"
              name="music"
              accept="audio/*"
              multiple
              onChange={handleMusicUpload}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none"
            />
          </div>
          
          <div className="flex justify-center pt-2">
            <button
              type="submit"
              className="px-6 py-2 bg-pink-500 text-white rounded-lg shadow hover:bg-pink-600 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-pink-400"
            >
              שמור
            </button>
          </div>
        </form>
      ) : (
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold mb-4">{formData.coupleName}</h2>
          {formData.venue && <p className="text-lg">מתחתנים ב{formData.venue}</p>}
          {formData.message && <p className="italic mt-2">{formData.message}</p>}
          <button
            onClick={() => setIsEditing(true)}
            className="mt-4 px-4 py-1 text-sm bg-transparent border border-pink-500 text-pink-600 rounded-full hover:bg-pink-50 transition-colors duration-300"
          >
            ערוך פרטים
          </button>
        </div>
      )}
    </div>
  );
};

export default WeddingDetails