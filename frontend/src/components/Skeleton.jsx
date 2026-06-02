export function SkeletonLine({ className = '' }) {
  return <span className={`skeleton-line ${className}`} />;
}

export function SkeletonRows({ rows = 5 }) {
  return (
    <div className="skeleton-rows">
      {Array.from({ length: rows }, (_, index) => (
        <div className="skeleton-row" key={index}>
          <SkeletonLine className="skeleton-line--short" />
          <SkeletonLine />
          <SkeletonLine className="skeleton-line--medium" />
        </div>
      ))}
    </div>
  );
}

export function DashboardSkeleton({ rows = 3 }) {
  return (
    <div className="dashboard-widget-list">
      {Array.from({ length: rows }, (_, index) => (
        <div className="dashboard-widget-row dashboard-widget-row--skeleton" key={index}>
          <SkeletonLine className="skeleton-line--time" />
          <div className="dashboard-widget-main">
            <SkeletonLine />
            <SkeletonLine className="skeleton-line--medium" />
            <SkeletonLine className="skeleton-line--long" />
          </div>
          <SkeletonLine className="skeleton-line--room" />
        </div>
      ))}
    </div>
  );
}

export function PageSkeleton({ widgets = 2 }) {
  return (
    <div className="skeleton-page-grid">
      {Array.from({ length: widgets }, (_, index) => (
        <div className="panel skeleton-panel" key={index}>
          <SkeletonLine className="skeleton-line--title" />
          <SkeletonRows rows={4} />
        </div>
      ))}
    </div>
  );
}
