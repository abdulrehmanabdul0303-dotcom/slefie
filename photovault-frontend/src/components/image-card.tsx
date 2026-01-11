'use client';

import { useState } from 'react';
import { MoreVertical, Trash2, Share2, Info } from 'lucide-react';
import { Modal, Button } from './ui';

export interface Image {
  id: string;
  url: string;
  thumbnail: string;
  name: string;
  size: number;
  uploadedAt: string;
  album?: string;
  tags?: string[];
}

interface ImageCardProps {
  image: Image;
  onDelete?: (id: string) => Promise<void>;
  onShare?: (id: string) => void;
  onInfo?: (image: Image) => void;
  selected?: boolean;
  onSelect?: (id: string) => void;
}

export function ImageCard({
  image,
  onDelete,
  onShare,
  onInfo,
  selected = false,
  onSelect,
}: ImageCardProps): React.ReactNode {
  const [showMenu, setShowMenu] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    if (!onDelete) return;
    setIsDeleting(true);
    try {
      await onDelete(image.id);
      setShowDeleteConfirm(false);
      setShowMenu(false);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div
        className={`relative group rounded-xl overflow-hidden border-2 cursor-pointer transition-all duration-200 ${
          selected
            ? 'border-blue-500/50 bg-blue-500/10'
            : 'border-white/10 hover:border-white/20 bg-white/5'
        }`}
        onClick={() => onSelect?.(image.id)}
      >
        {/* Image */}
        <img
          src={image.thumbnail || image.url}
          alt={image.name}
          className="w-full aspect-square object-cover"
        />

        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

        {/* Checkbox for selection */}
        {onSelect && (
          <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onSelect(image.id)}
              onClick={(e) => e.stopPropagation()}
              className="w-5 h-5 rounded border-2 border-white/30"
            />
          </div>
        )}

        {/* Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex gap-2 justify-between">
            <div className="flex gap-2">
              {onShare && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onShare(image.id);
                  }}
                  className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 transition-colors"
                  title="Share"
                >
                  <Share2 className="w-4 h-4 text-blue-300" />
                </button>
              )}
              {onInfo && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onInfo(image);
                  }}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 transition-colors"
                  title="Info"
                >
                  <Info className="w-4 h-4 text-white/70" />
                </button>
              )}
            </div>

            {/* Menu button */}
            {(onDelete || onShare) && (
              <div className="relative">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowMenu(!showMenu);
                  }}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 transition-colors"
                >
                  <MoreVertical className="w-4 h-4 text-white/70" />
                </button>

                {/* Dropdown menu */}
                {showMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-slate-800/95 backdrop-blur-md border border-white/10 rounded-lg shadow-xl overflow-hidden z-10">
                    {onShare && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onShare(image.id);
                          setShowMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-white hover:bg-white/10 flex items-center gap-2 transition-colors"
                      >
                        <Share2 className="w-4 h-4" />
                        Share
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(true);
                          setShowMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Image metadata */}
        <div className="absolute top-2 right-2 bg-black/60 rounded-lg px-2 py-1 text-xs text-white/70">
          {(image.size / (1024 * 1024)).toFixed(1)}MB
        </div>
      </div>

      {/* Delete confirmation modal */}
      <Modal isOpen={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} title="Delete Image">
        <div className="space-y-4">
          <p className="text-white/80">Are you sure you want to delete "{image.name}"? This action cannot be undone.</p>
          <div className="flex gap-3">
            <Button variant="secondary" fullWidth onClick={() => setShowDeleteConfirm(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              fullWidth
              loading={isDeleting}
              onClick={handleDelete}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
