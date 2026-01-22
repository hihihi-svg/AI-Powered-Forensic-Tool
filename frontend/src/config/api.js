// API Configuration
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8086';

export const API_ENDPOINTS = {
    START_GENERATION: `${API_URL}/api/start-generation`,
    CHECK_STATUS: `${API_URL}/api/check-status`,
    VERIFY_AND_SEARCH: `${API_URL}/api/verify-and-search`,
    DETECT_DEEPFAKE: `${API_URL}/api/detect-deepfake`,
    UPLOAD_IMAGE: `${API_URL}/api/upload-image`,
    SEARCH: `${API_URL}/api/search`,

    // CRUD Endpoints
    SUSPECTS: `${API_URL}/api/suspects`,
    SUSPECTS_STATS: `${API_URL}/api/suspects/stats/overview`,
    SUSPECTS_BULK_DELETE: `${API_URL}/api/suspects/bulk-delete`,
};
