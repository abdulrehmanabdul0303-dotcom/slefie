"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Menu } from "lucide-react";

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const [q, setQ] = useState("");
  const router = useRouter();

  return (
    <header className="sticky top-0 z-10 bg-white border-b p-3 flex items-center gap-3">
      <button
        onClick={onMenuClick}
        className="md:hidden p-2 hover:bg-gray-100 rounded-md"
        aria-label="Open menu"
      >
        <Menu size={24} />
      </button>
      <div className="md:hidden font-bold text-lg">PhotoVault</div>
      <form
        className="flex-1 min-w-0"
        onSubmit={(e) => {
          e.preventDefault();
          router.push(`/search?q=${encodeURIComponent(q)}`);
        }}
      >
        <input
          className="w-full border rounded-md px-3 py-2 text-sm"
          placeholder="Quick search..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </form>
    </header>
  );
}
