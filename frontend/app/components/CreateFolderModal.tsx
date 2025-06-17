import React from 'react';

interface CreateFolderModalProps {
  isOpen: boolean;
  folderName: string;
  onNameChange: (name: string) => void;
  onCancel: () => void;
  onCreate: () => void;
}

export default function CreateFolderModal({
  isOpen,
  folderName,
  onNameChange,
  onCancel,
  onCreate
}: CreateFolderModalProps) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-xl font-bold mb-4">Create New Folder</h3>
        <input
          type="text"
          value={folderName}
          onChange={(e) => onNameChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onCreate()}
          placeholder="Folder name"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoFocus
        />
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
} 