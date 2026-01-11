export default function EmptyState({ 
  message, 
  icon 
}: { 
  message?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      {icon && <div className="mb-4 text-gray-400">{icon}</div>}
      <p className="text-gray-500 text-sm">{message || "No data available"}</p>
    </div>
  );
}

