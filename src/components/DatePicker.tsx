import React, { useState } from 'react';

interface DatePickerProps {
  selectedDate: Date | null;
  onChange: (date: Date) => void;
  className?: string;
}

const DatePicker: React.FC<DatePickerProps> = ({ selectedDate, onChange, className = '' }) => {
  const [dateValue, setDateValue] = useState<string>(
    selectedDate 
      ? `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}T${String(selectedDate.getHours()).padStart(2, '0')}:${String(selectedDate.getMinutes()).padStart(2, '0')}`
      : ''
  );

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDateString = e.target.value;
    setDateValue(newDateString);
    
    if (newDateString) {
      const newDate = new Date(newDateString);
      onChange(newDate);
    }
  };

  return (
    <div className={`flex flex-col ${className}`}>
      <label htmlFor="weddingDate" className="mb-2 font-medium text-right">
        תאריך ושעת החתונה:
      </label>
      <input
        type="datetime-local"
        id="weddingDate"
        value={dateValue}
        onChange={handleDateChange}
        className="bg-white bg-opacity-90 backdrop-blur-sm p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-pink-400 focus:border-pink-400 outline-none text-right"
        dir="rtl"
      />
    </div>
  );
};

export default DatePicker;