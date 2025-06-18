import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import HealthCheck from './components/HealthCheck'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Chat PDF',
  description: 'Chat with your PDF documents using AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <HealthCheck />
      </body>
    </html>
  )
}