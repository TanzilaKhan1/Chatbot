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
      await api.uploadFile(file, folderId)
      await fetchFiles()
    } catch (error) {
      console.error('Error uploading file:', error)
      throw error; // Re-throw to let the modal handle the error
    } finally {
      setIsUploading(false)
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