export interface WeddingDetails {
  coupleName: string;
  weddingDate: Date | null;
  venue: string;
  message: string;
  photos: string[];
  music: string[];
}

export interface CountdownValues {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

export interface ThemeOption {
  id: string;
  name: string;
  bgClass: string;
  textClass: string;
}