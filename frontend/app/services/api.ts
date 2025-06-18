// app/services/api.ts
// This file now re-exports everything from the modular structure for backward compatibility
// Consumers of this API should gradually migrate to importing directly from the modular services

export * from './apiClient';
export * from './healthApi';
export * from './folderApi';
export * from './fileApi';
export * from './chatApi';
export * from './sessionApi';
export * from '../types/api';