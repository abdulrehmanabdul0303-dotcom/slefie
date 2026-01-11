"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

/**
 * Glassmorphism Card Component
 * Floating layers with soft depth
 */
export function GlassCard({ children, className = "", hover = true, onClick }: GlassCardProps) {
  return (
    <motion.div
      className={`glass rounded-2xl p-6 ${className}`}
      whileHover={hover ? { 
        scale: 1.02,
        y: -4,
        boxShadow: "0 12px 40px 0 rgba(31, 38, 135, 0.5)"
      } : {}}
      whileTap={onClick ? { scale: 0.98 } : {}}
      onClick={onClick}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      {children}
    </motion.div>
  );
}

