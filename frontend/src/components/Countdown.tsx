import { useState, useEffect } from 'react';

interface CountdownProps {
  targetTime: string; // ISO datetime string
  onComplete?: () => void;
}

export function Countdown({ targetTime, onComplete }: CountdownProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const target = new Date(targetTime);
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining('Now');
        setIsCompleted(true);
        onComplete?.();
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      let formatted = '';
      if (days > 0) {
        formatted = `${days}d ${hours}h ${minutes}m`;
      } else if (hours > 0) {
        formatted = `${hours}h ${minutes}m ${seconds}s`;
      } else if (minutes > 0) {
        formatted = `${minutes}m ${seconds}s`;
      } else {
        formatted = `${seconds}s`;
      }

      setTimeRemaining(formatted);
      setIsCompleted(false);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [targetTime, onComplete]);

  return (
    <span className={`font-medium ${isCompleted ? 'text-green-600' : 'text-gray-900'}`}>
      {timeRemaining || '...'}
    </span>
  );
}
