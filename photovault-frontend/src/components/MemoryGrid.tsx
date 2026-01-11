"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { GlassCard } from "./GlassCard";

interface Memory {
  id: string;
  url: string;
  thumbnail?: string;
  date?: string;
  title?: string;
}

interface MemoryGridProps {
  memories: Memory[];
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

/**
 * Memory Grid - Responsive, animated grid with hover previews
 * Infinite scroll / lazy loading
 */
export function MemoryGrid({ memories, loading = false, onLoadMore, hasMore = false }: MemoryGridProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Infinite scroll
  useEffect(() => {
    if (!onLoadMore || !hasMore) return;

    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 1000
      ) {
        onLoadMore();
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [onLoadMore, hasMore]);

  // Skeleton loader
  const SkeletonCard = () => (
    <div className="aspect-square rounded-2xl skeleton overflow-hidden" />
  );

  if (loading && memories.length === 0) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 p-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <GlassCard>
          <p className="text-white/60 text-center">No memories found</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 p-4">
        <AnimatePresence mode="popLayout">
          {memories.map((memory, index) => (
            <motion.div
              key={memory.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: index * 0.02 }}
              onHoverStart={() => setHoveredId(memory.id)}
              onHoverEnd={() => setHoveredId(null)}
              className="relative group"
            >
              <GlassCard hover>
                <div className="aspect-square relative overflow-hidden rounded-xl">
                  {memory.thumbnail || memory.url ? (
                    <Image
                      src={memory.thumbnail || memory.url}
                      alt={memory.title || "Memory"}
                      fill
                      className="object-cover transition-transform duration-300 group-hover:scale-110"
                      sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
                      unoptimized={memory.url?.startsWith("http") ? false : true}
                    />
                  ) : (
                    <div className="w-full h-full bg-white/10 flex items-center justify-center">
                      <span className="text-white/40 text-xs">No image</span>
                    </div>
                  )}
                  
                  {/* Hover overlay */}
                  <AnimatePresence>
                    {hoveredId === memory.id && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/40 flex items-center justify-center"
                      >
                        {memory.date && (
                          <motion.p
                            initial={{ y: 10 }}
                            animate={{ y: 0 }}
                            className="text-white text-sm"
                          >
                            {new Date(memory.date).toLocaleDateString()}
                          </motion.p>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Loading more skeletons */}
      {loading && memories.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 p-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={`loading-${i}`} />
          ))}
        </div>
      )}
    </>
  );
}

