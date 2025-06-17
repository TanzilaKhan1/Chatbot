'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { FolderWithFiles } from './types'
import * as api from './services/api'
import TopNavigation from './components/TopNavigation'
import FolderCard from './components/FolderCard'
import CreateFolderCard from './components/CreateFolderCard'
import CreateFolderModal from './components/CreateFolderModal'
import LoadingSpinner from './components/LoadingSpinner'

export default function Home() {
  const router = useRouter()
  const [folders, setFolders] = useState<FolderWithFiles[]>([])
  const [newFolderName, setNewFolderName] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set())

  // Fetch folders from API
  const fetchFolders = async () => {
    try {
      setLoading(true)
      const foldersData = await api.fetchFolders()
      
      // Map API response to include fileCount
      const foldersWithFiles = await Promise.all(
        foldersData.map(async (folder) => {
          try {
            const filesData = await api.fetchFolderFiles(folder.id)
            return {
              ...folder,
              fileCount: filesData.length
            }
          } catch (error) {
            console.error(`Error fetching files for folder ${folder.id}:`, error)
            return {
              ...folder,
              fileCount: 0
            }
          }
        })
      )
      
      setFolders(foldersWithFiles)
    } catch (error) {
      console.error('Error fetching folders:', error)
    } finally {
      setLoading(false)
    }
  }

  // Create folder
  const createFolder = async () => {
    if (!newFolderName.trim()) return

    try {
      await api.createFolder(newFolderName)
      
      setNewFolderName('')
      setShowCreateModal(false)
      fetchFolders()
    } catch (error) {
      console.error('Error creating folder:', error)
      alert('Failed to create folder')
    }
  }

  // Delete selected folders
  const deleteSelectedFolders = async () => {
    if (selectedFolders.size === 0) {
      alert('Please select folders to delete')
      return
    }

    if (!confirm(`Are you sure you want to delete ${selectedFolders.size} folder(s)?`)) return

    try {
      await Promise.all(
        Array.from(selectedFolders).map(folderId =>
          api.deleteFolder(folderId)
        )
      )
      
      setSelectedFolders(new Set())
      fetchFolders()
    } catch (error) {
      console.error('Error deleting folders:', error)
      alert('Failed to delete some folders')
    }
  }

  // Toggle folder selection
  const toggleFolderSelection = (folderId: string) => {
    const newSelection = new Set(selectedFolders)
    if (newSelection.has(folderId)) {
      newSelection.delete(folderId)
    } else {
      newSelection.add(folderId)
    }
    setSelectedFolders(newSelection)
  }

  // Navigate to folder details
  const navigateToFolder = (folder: FolderWithFiles) => {
    router.push(`/folder/${folder.id}?name=${encodeURIComponent(folder.name)}`)
  }

  useEffect(() => {
    fetchFolders()
  }, [])

  const folderColors = [
    'bg-purple-100',   // Lavender
    'bg-yellow-100',   // Light Yellow
    'bg-blue-100',     // Light Blue
    'bg-pink-100',     // Light Pink
    'bg-green-100',    // Light Green
    'bg-orange-100'    // Light Orange
  ]
  
  const iconColors = [
    'text-purple-400',  // Softer Lavender
    'text-yellow-500',  // Slightly deeper Yellow
    'text-blue-400',    // Sky Blue
    'text-pink-400',    // Rosy Pink
    'text-green-500',   // Fresh Mint
    'text-orange-400'   // Peachy Orange
  ]

  
  return (
    <div className="min-h-screen bg-gray-50">
      <TopNavigation 
        title="File Manager" 
        onCreateFolder={() => setShowCreateModal(true)} 
        onDeleteFolders={deleteSelectedFolders} 
      />

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-6">Folders</h2>
        
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {folders.map((folder, index) => (
              <FolderCard
                key={folder.id}
                folder={folder}
                index={index}
                isSelected={selectedFolders.has(folder.id)}
                onSelect={toggleFolderSelection}
                onNavigate={navigateToFolder}
                folderColors={folderColors}
                iconColors={iconColors}
              />
            ))}
            
            <CreateFolderCard onClick={() => setShowCreateModal(true)} />
          </div>
        )}
      </div>

      <CreateFolderModal
        isOpen={showCreateModal}
        folderName={newFolderName}
        onNameChange={setNewFolderName}
        onCancel={() => {
          setShowCreateModal(false)
          setNewFolderName('')
        }}
        onCreate={createFolder}
      />
    </div>
  )
}