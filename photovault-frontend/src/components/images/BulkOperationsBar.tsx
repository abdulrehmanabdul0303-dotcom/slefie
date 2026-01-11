"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import { Trash2, X, CheckSquare, Square } from "lucide-react";

interface BulkOperationsBarProps {
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  onDeleteComplete: () => void;
  totalCount: number;
}

export function BulkOperationsBar({
  selectedIds,
  onSelectionChange,
  onDeleteComplete,
  totalCount,
}: BulkOperationsBarProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const selectedCount = selectedIds.size;
  const allSelected = selectedCount === totalCount && totalCount > 0;

  function toggleSelectAll() {
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      // Select all would require fetching all IDs, so we'll just clear for now
      // In a real implementation, you might want to track all IDs
      onSelectionChange(new Set());
    }
  }

  async function handleBulkDelete() {
    if (selectedIds.size === 0) {
      toast.error("No images selected");
      return;
    }

    if (!confirm(`Delete ${selectedIds.size} image(s)? This cannot be undone.`)) {
      return;
    }

    setIsDeleting(true);

    try {
      // Fetch CSRF token
      try {
        const csrfRes = await api.get(endpoints.csrf);
        const csrfToken = csrfRes.data?.csrfToken ?? csrfRes.data;
        if (csrfToken) {
          // CSRF will be handled by interceptor
        }
      } catch (csrfError) {
        console.warn("Failed to fetch CSRF token:", csrfError);
      }

      const imageIds = Array.from(selectedIds);
      const response = await api.post(endpoints.imageBulkDelete, imageIds);

      const deleted = response.data?.deleted ?? 0;
      const failed = response.data?.failed ?? 0;

      if (deleted > 0) {
        toast.success(`Deleted ${deleted} image(s)`);
      }
      if (failed > 0) {
        toast.error(`Failed to delete ${failed} image(s)`);
      }

      // Clear selection
      onSelectionChange(new Set());
      
      // Refresh the list
      onDeleteComplete();
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail ?? e?.message ?? "Failed to delete images";
      toast.error(errorMsg);
    } finally {
      setIsDeleting(false);
    }
  }

  if (selectedCount === 0) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 sm:p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
      <div className="flex items-center gap-2 sm:gap-4">
        <button
          onClick={toggleSelectAll}
          className="p-2 hover:bg-blue-100 rounded min-w-[44px] min-h-[44px] flex items-center justify-center"
          title={allSelected ? "Deselect all" : "Select all"}
        >
          {allSelected ? (
            <CheckSquare className="h-5 w-5 text-blue-600" />
          ) : (
            <Square className="h-5 w-5 text-blue-600" />
          )}
        </button>
        <span className="text-xs sm:text-sm font-medium text-blue-900">
          {selectedCount} image{selectedCount !== 1 ? "s" : ""} selected
        </span>
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto">
        <button
          onClick={() => onSelectionChange(new Set())}
          className="flex-1 sm:flex-none px-3 py-2.5 text-sm text-blue-700 hover:bg-blue-100 rounded-md transition-colors min-h-[44px] flex items-center justify-center gap-1"
          disabled={isDeleting}
        >
          <X className="h-4 w-4" />
          <span className="sm:inline">Clear</span>
        </button>
        <button
          onClick={handleBulkDelete}
          disabled={isDeleting || selectedCount === 0}
          className="flex-1 sm:flex-none px-3 py-2.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1 min-h-[44px]"
        >
          <Trash2 className="h-4 w-4" />
          <span>{isDeleting ? "Deleting..." : `Delete ${selectedCount}`}</span>
        </button>
      </div>
    </div>
  );
}

