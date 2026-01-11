export default function Loading({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <span className="ml-3 text-gray-600">{message || "Loading..."}</span>
    </div>
  );
}

