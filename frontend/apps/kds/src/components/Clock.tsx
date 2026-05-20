import React, { useState, useEffect, memo } from 'react';

const Clock: React.FC = memo(() => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <span className="text-lg font-mono text-white">
      {time.toLocaleTimeString()}
    </span>
  );
});

Clock.displayName = 'Clock';
export { Clock };
