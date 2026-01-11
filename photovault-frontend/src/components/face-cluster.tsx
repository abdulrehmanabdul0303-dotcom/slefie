'use client';

import { useState } from 'react';
import { Users, Edit2, Trash2 } from 'lucide-react';
import { Button, Modal } from './ui';

export interface FaceCluster {
  id: string;
  name?: string;
  imageCount: number;
  representative?: string; // URL of representative image
  faces: string[]; // Array of image IDs
}

interface FaceClusterCardProps {
  cluster: FaceCluster;
  onRename?: (id: string, name: string) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  onClick?: () => void;
}

export function FaceClusterCard({
  cluster,
  onRename,
  onDelete,
  onClick,
}: FaceClusterCardProps): React.ReactNode {
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [newName, setNewName] = useState(cluster.name || '');
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleRename = async () => {
    if (!onRename || !newName.trim()) return;
    setIsLoading(true);
    try {
      await onRename(cluster.id, newName);
      setShowRenameModal(false);
    } catch (error) {
      console.error('Rename failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete) return;
    setIsLoading(true);
    try {
      await onDelete(cluster.id);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div
        onClick={onClick}
        className="group cursor-pointer rounded-xl overflow-hidden border border-white/10 hover:border-white/20 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10 bg-white/5"
      >
        {/* Cover image */}
        <div className="relative w-full aspect-square bg-gradient-to-br from-purple-500/10 to-pink-500/10 overflow-hidden">
          {cluster.representative ? (
            <img
              src={cluster.representative}
              alt={cluster.name || 'Face cluster'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Users className="w-12 h-12 text-white/30" />
            </div>
          )}

          {/* Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

          {/* Actions */}
          <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {onRename && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowRenameModal(true);
                }}
                className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 transition-colors"
                title="Rename"
              >
                <Edit2 className="w-4 h-4 text-blue-300" />
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

        {/* Cluster info */}
        <div className="p-4">
          <h3 className="font-medium text-white truncate">
            {cluster.name || 'Unknown Person'}
          </h3>
          <p className="text-sm text-white/50 mt-1">
            {cluster.imageCount} appearance{cluster.imageCount !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Rename modal */}
      <Modal
        isOpen={showRenameModal}
        onClose={() => setShowRenameModal(false)}
        title="Rename Person"
      >
        <div className="space-y-4">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Enter name..."
            className="w-full px-4 py-2.5 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
          />
          <div className="flex gap-3">
            <Button
              variant="secondary"
              fullWidth
              onClick={() => setShowRenameModal(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              fullWidth
              loading={isLoading}
              onClick={handleRename}
              disabled={!newName.trim() || isLoading}
            >
              Rename
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete confirmation modal */}
      <Modal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Person"
      >
        <div className="space-y-4">
          <p className="text-white/80">
            Are you sure you want to delete "{cluster.name || 'Unknown Person'}"?
            This will not delete the photos, only the face cluster.
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
              loading={isLoading}
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
