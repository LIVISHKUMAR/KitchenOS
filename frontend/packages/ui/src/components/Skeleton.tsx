import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  count = 1,
}) => {
  const baseStyles = 'animate-pulse bg-gray-200';

  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  if (variant === 'text' && !height) {
    style.height = '1rem';
  }

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`${baseStyles} ${variantStyles[variant]} ${className}`}
          style={style}
        />
      ))}
    </>
  );
};

// Pre-built skeleton patterns
export const StatCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-xl p-4 border border-gray-100">
    <Skeleton width="40%" height="0.875rem" className="mb-2" />
    <Skeleton width="60%" height="2rem" className="mb-1" />
    <Skeleton width="30%" height="0.75rem" />
  </div>
);

export const TableRowSkeleton: React.FC<{ columns?: number }> = ({ columns = 4 }) => (
  <tr>
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-6 py-4">
        <Skeleton width={i === 0 ? '80%' : '60%'} />
      </td>
    ))}
  </tr>
);
