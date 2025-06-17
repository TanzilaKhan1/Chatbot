import React from 'react';

interface FolderWithFiles {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  created_at: string;
  updated_at: string;
  fileCount: number;
}

interface FolderCardProps {
  folder: FolderWithFiles;
  index: number;
  isSelected: boolean;
  onSelect: (folderId: string) => void;
  onNavigate: (folder: FolderWithFiles) => void;
  folderColors: string[];
  iconColors: string[];
}

export default function FolderCard({
  folder,
  index,
  isSelected,
  onSelect,
  onNavigate,
  folderColors,
  iconColors
}: FolderCardProps) {
  return (
    <div className="relative group">
      <div
        onClick={() => onNavigate(folder)}
        className={`${folderColors[index % folderColors.length]} rounded-2xl p-6 cursor-pointer transition-all hover:scale-105 hover:shadow-lg`}
      >
        <div className="flex flex-col items-center">
          <div className={`w-16 h-16 ${iconColors[index % iconColors.length]} mb-3`}>
            <svg fill="currentColor" viewBox="0 0 24 24">
              <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
            </svg>
          </div>
          <span className="text-2xl font-bold text-gray-800">{folder.fileCount}</span>
          <span className="text-sm text-gray-600">Files</span>
          <span className="text-xs text-gray-500 mt-2 text-center truncate w-full px-2">
            {folder.name}
          </span>
        </div>
      </div>
      
      {/* Selection Checkbox */}
      <div
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          onSelect(folder.id);
        }}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => {}}
          className="w-5 h-5 cursor-pointer"
        />
      </div>
    </div>
  );
} 