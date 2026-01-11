'use client';

import { useState } from 'react';
import { Plus, Pencil, Trash2, Images } from 'lucide-react';
import { Button, Modal, Input } from './ui';

export interface Album {
  id: string;
  name: string;
  description?: string;
  coverImage?: string;
  imageCount: number;
  createdAt: string;
  updatedAt: string;
}

interface AlbumCardProps {
  album: Album;
  onEdit?: (album: Album) => void;
  onDelete?: (id: string) => Promise<void>;
  onClick?: () => void;
}

export function AlbumCard({
  album,
  onEdit,
  onDelete,
  onClick,
}: AlbumCardProps): React.ReactNode {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!onDelete) return;
    setIsDeleting(true);
    try {
      await onDelete(album.id);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div
        onClick={onClick}
        className="group cursor-pointer rounded-xl overflow-hidden border border-white/10 hover:border-white/20 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10 bg-white/5"
      >
        {/* Cover image */}
        <div className="relative w-full aspect-square bg-gradient-to-br from-blue-500/10 to-cyan-500/10 overflow-hidden">
          {album.coverImage ? (
            <img
              src={album.coverImage}
              alt={album.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Images className="w-12 h-12 text-white/30" />
            </div>
          )}

          {/* Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

          {/* Actions */}
          <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {onEdit && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(album);
                }}
                className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 transition-colors"
                title="Edit"
              >
                <Pencil className="w-4 h-4 text-blue-300" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDeleteConfirm(true);
                }}
                className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4 text-red-300" />
              </button>
            )}
          </div>
        </div>

        {/* Album info */}
        <div className="p-4">
          <h3 className="font-medium text-white truncate">{album.name}</h3>
          <p className="text-sm text-white/50 mt-1">{album.imageCount} photos</p>
          {album.description && (
            <p className="text-xs text-white/40 mt-2 line-clamp-2">{album.description}</p>
          )}
        </div>
      </div>

      {/* Delete confirmation modal */}
      <Modal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Album"
      >
        <div className="space-y-4">
          <p className="text-white/80">
            Are you sure you want to delete "{album.name}"? This action cannot be undone.
          </p>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              fullWidth
              onClick={() => setShowDeleteConfirm(false)}
            >
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

interface AlbumCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; description?: string }) => Promise<void>;
  initialData?: Album;
}

export function AlbumCreateModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
}: AlbumCreateModalProps): React.ReactNode {
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsLoading(true);
    try {
      await onSubmit({ name, description });
      setName('');
      setDescription('');
      onClose();
    } catch (error) {
      console.error('Create/update failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Edit Album' : 'Create Album'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Album Name"
          placeholder="My Vacation"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={isLoading}
        />
        <Input
          label="Description (optional)"
          placeholder="Add a description..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isLoading}
        />
        <div className="flex gap-3 pt-2">
          <Button
            variant="secondary"
            fullWidth
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            fullWidth
            type="submit"
            loading={isLoading}
            disabled={!name.trim() || isLoading}
          >
            {initialData ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
