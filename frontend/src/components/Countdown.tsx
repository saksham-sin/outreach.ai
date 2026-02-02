import { useState, useEffect, useRef } from 'react';

interface CountdownProps {
  readonly targetTime: string; // ISO datetime string
  readonly onComplete?: () => void;
}

export function Countdown({ targetTime, onComplete }: CountdownProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [isCompleted, setIsCompleted] = useState(false);
  const hasCompletedRef = useRef(false);

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const target = new Date(targetTime);
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining('Sent');
        setIsCompleted(true);
        if (!hasCompletedRef.current) {
          hasCompletedRef.current = true;
          onComplete?.();
        }
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

    hasCompletedRef.current = false;
    updateCountdown();
    const interval = setInterval(() => {
      updateCountdown();
      if (hasCompletedRef.current) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [targetTime, onComplete]);

  return (
    <span className={`font-medium tabular-nums ${isCompleted ? 'text-green-600' : 'text-gray-900'}`}>
      {timeRemaining || '...'}
    </span>
  );
}
