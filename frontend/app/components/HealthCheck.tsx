'use client';

import React, { useState, useEffect } from 'react';
import { healthCheck, checkConfig, checkSimpleChatHealth } from '../services/api';

interface HealthStatus {
  backend: 'loading' | 'healthy' | 'unhealthy';
  config: 'loading' | 'healthy' | 'unhealthy';
  chat: 'loading' | 'healthy' | 'unhealthy';
  details: {
    backend?: any;
    config?: any;
    chat?: any;
  };
}

interface HealthResponse {
  status: string;
  [key: string]: any;
}

export default function HealthCheck() {
  const [health, setHealth] = useState<HealthStatus>({
    backend: 'loading',
    config: 'loading',
    chat: 'loading',
    details: {}
  });
  const [isVisible, setIsVisible] = useState(false);

  const checkHealth = async () => {
    setHealth(prev => ({
      ...prev,
      backend: 'loading',
      config: 'loading',
      chat: 'loading'
    }));

    // Check backend health
    try {
      const backendHealth = await healthCheck() as HealthResponse;
      setHealth(prev => ({
        ...prev,
        backend: backendHealth.status === 'healthy' ? 'healthy' : 'unhealthy',
        details: { ...prev.details, backend: backendHealth }
      }));
    } catch (error) {
      setHealth(prev => ({
        ...prev,
        backend: 'unhealthy',
        details: { ...prev.details, backend: { error: 'Connection failed' } }
      }));
    }

    // Check config
    try {
      const configCheck = await checkConfig();
      setHealth(prev => ({
        ...prev,
        config: 'healthy',
        details: { ...prev.details, config: configCheck }
      }));
    } catch (error) {
      setHealth(prev => ({
        ...prev,
        config: 'unhealthy',
        details: { ...prev.details, config: { error: 'Config check failed' } }
      }));
    }

    // Check chat health
    try {
      const chatHealth = await checkSimpleChatHealth() as HealthResponse;
      setHealth(prev => ({
        ...prev,
        chat: chatHealth.status === 'healthy' ? 'healthy' : 'unhealthy',
        details: { ...prev.details, chat: chatHealth }
      }));
    } catch (error) {
      setHealth(prev => ({
        ...prev,
        chat: 'unhealthy',
        details: { ...prev.details, chat: { error: 'Chat service unavailable' } }
      }));
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'unhealthy': return 'text-red-600';
      case 'loading': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'unhealthy': return '❌';
      case 'loading': return '⏳';
      default: return '❓';
    }
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 p-2 bg-gray-800 text-white rounded-full hover:bg-gray-700 transition-colors z-50"
        title="System Health"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-800">System Health</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center">
          <span>Backend:</span>
          <span className={`flex items-center gap-1 ${getStatusColor(health.backend)}`}>
            {getStatusIcon(health.backend)} {health.backend}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span>Configuration:</span>
          <span className={`flex items-center gap-1 ${getStatusColor(health.config)}`}>
            {getStatusIcon(health.config)} {health.config}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span>Chat Service:</span>
          <span className={`flex items-center gap-1 ${getStatusColor(health.chat)}`}>
            {getStatusIcon(health.chat)} {health.chat}
          </span>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t">
        <button
          onClick={checkHealth}
          className="w-full px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
        >
          Refresh
        </button>
      </div>
      
      {(health.backend === 'unhealthy' || health.config === 'unhealthy' || health.chat === 'unhealthy') && (
        <div className="mt-2 p-2 bg-red-50 text-red-800 rounded text-xs">
          Some services are not working properly. Check the backend configuration.
        </div>
      )}
    </div>
  );
} 