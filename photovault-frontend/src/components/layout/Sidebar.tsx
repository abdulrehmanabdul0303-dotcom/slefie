"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Image as ImgIcon, Album, Search, Users, Shield, Settings, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-provider";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/images", label: "Images", icon: ImgIcon },
  { href: "/albums", label: "Albums", icon: Album },
  { href: "/search", label: "Search", icon: Search },
  { href: "/persons", label: "People", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-white">
      <div className="p-4 border-b">
        <div className="font-bold text-lg">PhotoVault</div>
        <div className="text-xs text-gray-500 truncate">{user?.email}</div>
      </div>

      <nav className="p-2 flex-1">
        {nav.map((item) => {
          const ActiveIcon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
                active ? "bg-gray-100 font-medium" : "hover:bg-gray-50"
              }`}
            >
              <ActiveIcon size={18} />
              {item.label}
            </Link>
          );
        })}

        {user?.is_admin && (
          <Link
            href="/admin"
            className={`mt-2 flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
              pathname === "/admin" ? "bg-gray-100 font-medium" : "hover:bg-gray-50"
            }`}
          >
            <Shield size={18} />
            Admin
          </Link>
        )}
      </nav>

      <button
        onClick={logout}
        className="m-2 flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-50 border"
      >
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  );
}
