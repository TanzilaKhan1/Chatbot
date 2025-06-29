import React from 'react';

export default function EmptyFilesPlaceholder() {
  return (
    <div className="text-center py-12">
      <svg className="w-24 h-24 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
      <p className="text-gray-500 text-lg">No files in this folder</p>
      <p className="text-gray-400 mt-2">Upload a PDF file to get started</p>
    </div>
  );
} 