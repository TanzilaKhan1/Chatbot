'use client'

import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import { FileItem } from '../../types'
import * as api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'
import FileTable from '../../components/FileTable'
import EmptyFilesPlaceholder from '../../components/EmptyFilesPlaceholder'
import FolderHeader from '../../components/FolderHeader'
import UploadModal from '../../components/UploadModal'

export default function FolderDetail() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const folderId = params.id as string
  const folderName = searchParams.get('name') || 'Folder'
  
  const [files, setFiles] = useState<FileItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)

  // Fetch files
  const fetchFiles = async () => {
    try {
      setLoading(true)
      const filesData = await api.fetchFolderFiles(folderId)
      setFiles(filesData)
    } catch (error) {
      console.error('Error fetching files:', error)
    } finally {
      setLoading(false)
    }
  }

  // Upload file
  const uploadFile = async (file: File) => {
    setIsUploading(true)
    
    try {
      // Upload file to Supabase
      const uploadResponse = await api.uploadFile(file, folderId)
      
      // Set processing state to true while vectors are being generated
      setIsProcessing(true)
      setIsUploading(false)
      
      // Wait a bit to allow vector processing to start on the backend
      setTimeout(async () => {
        // Fetch updated files list
        await fetchFiles()
        setIsProcessing(false)
      }, 2000) // Give backend time to start processing
    } catch (error) {
      console.error('Error uploading file:', error)
      setIsUploading(false)
      setIsProcessing(false)
      throw error; // Re-throw to let the modal handle the error
    }
  }

  // Delete file
  const deleteFile = async (fileId: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return

    try {
      await api.deleteFile(fileId)
      fetchFiles()
    } catch (error) {
      console.error('Error deleting file:', error)
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [folderId])

  return (
    <div className="min-h-screen bg-gray-50">
      <FolderHeader 
        folderName={folderName}
        folderId={folderId}
        onBack={() => router.push('/')}
        onUploadClick={() => setShowUploadModal(true)}
      />

      {/* Files List */}
      <div className="container mx-auto px-6 py-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-6">Files</h2>
        
        {isProcessing && (
          <div className="mb-4 bg-blue-50 p-4 rounded-md flex items-center text-blue-700">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
            <span>Processing document for AI search capabilities...</span>
          </div>
        )}
        
        {loading ? (
          <LoadingSpinner />
        ) : files.length === 0 ? (
          <EmptyFilesPlaceholder />
        ) : (
          <FileTable files={files} onDelete={deleteFile} />
        )}
      </div>

      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={uploadFile}
        isUploading={isUploading}
      />
    </div>
  )
} 