"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Image as ImgIcon, Album, Search, Users, Shield, Settings, LogOut, X } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-provider";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/images", label: "Images", icon: ImgIcon },
  { href: "/albums", label: "Albums", icon: Album },
  { href: "/search", label: "Search", icon: Search },
  { href: "/persons", label: "People", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MobileSidebar({ isOpen, onClose }: MobileSidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40 md:hidden"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 bg-white z-50 md:hidden flex flex-col shadow-xl">
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <div className="font-bold text-lg">PhotoVault</div>
            <div className="text-xs text-gray-500 truncate">{user?.email}</div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-md"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="p-2 flex-1 overflow-y-auto">
          {nav.map((item) => {
            const ActiveIcon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-3 rounded-md text-sm ${
                  active ? "bg-gray-100 font-medium" : "hover:bg-gray-50"
                }`}
              >
                <ActiveIcon size={20} />
                {item.label}
              </Link>
            );
          })}

          {user?.is_admin && (
            <Link
              href="/admin"
              onClick={onClose}
              className={`mt-2 flex items-center gap-3 px-3 py-3 rounded-md text-sm ${
                pathname === "/admin" ? "bg-gray-100 font-medium" : "hover:bg-gray-50"
              }`}
            >
              <Shield size={20} />
              Admin
            </Link>
          )}
        </nav>

        <button
          onClick={() => {
            onClose();
            logout();
          }}
          className="m-2 flex items-center gap-3 px-3 py-3 rounded-md text-sm hover:bg-gray-50 border"
        >
          <LogOut size={20} />
          Logout
        </button>
      </aside>
    </>
  );
}

