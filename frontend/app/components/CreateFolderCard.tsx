import React from 'react';

interface CreateFolderCardProps {
  onClick: () => void;
}

export default function CreateFolderCard({ onClick }: CreateFolderCardProps) {
  return (
    <div
      onClick={onClick}
      className="border-2 border-dashed border-gray-300 rounded-2xl p-6 cursor-pointer transition-all hover:scale-105 hover:border-gray-400 bg-white"
    >
      <div className="flex flex-col items-center justify-center h-full">
        <svg className="w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        <span className="text-gray-600 font-medium">Create Folder</span>
      </div>
    </div>
  );
} 