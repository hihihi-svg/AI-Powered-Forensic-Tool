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

    // Session Management Endpoints
    SESSIONS: `${API_URL}/api/sessions`,
    SESSION_BY_ID: (sessionId) => `${API_URL}/api/sessions/${sessionId}`,
    SESSION_HISTORY: (sessionId) => `${API_URL}/api/sessions/${sessionId}/history`,
    SESSION_INTERACTIONS: (sessionId) => `${API_URL}/api/sessions/${sessionId}/interactions`,
    SESSION_CONTEXT: (sessionId) => `${API_URL}/api/sessions/${sessionId}/context`,
    MEMORY_STATS: (suspectId) => `${API_URL}/api/memory/stats/${suspectId}`,
};

// Session Management Utilities
const SESSION_STORAGE_KEY = 'forensic_tool_session_id';

export const SessionManager = {
    /**
     * Get or create a session ID
     */
    async getSessionId() {
        try {
            // Check localStorage for existing session
            let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);

            if (sessionId) {
                // Verify session is still valid
                const response = await fetch(API_ENDPOINTS.SESSION_BY_ID(sessionId));
                if (response.ok) {
                    return sessionId;
                }
            }

            // Create new session
            const response = await fetch(API_ENDPOINTS.SESSIONS, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: 'web_user' })
            });

            if (response.ok) {
                const data = await response.json();
                sessionId = data.session_id;
                localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
                return sessionId;
            }

            return null;
        } catch (error) {
            console.error('Error managing session:', error);
            return null;
        }
    },

    /**
     * Log an interaction to the current session
     */
    async logInteraction(interactionType, query = null, results = null, metadata = null) {
        try {
            const sessionId = await this.getSessionId();
            if (!sessionId) return false;

            const response = await fetch(API_ENDPOINTS.SESSION_INTERACTIONS(sessionId), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    interaction_type: interactionType,
                    query,
                    results,
                    metadata
                })
            });

            return response.ok;
        } catch (error) {
            console.error('Error logging interaction:', error);
            return false;
        }
    },

    /**
     * Get session history
     */
    async getHistory(limit = 50) {
        try {
            const sessionId = await this.getSessionId();
            if (!sessionId) return [];

            const response = await fetch(API_ENDPOINTS.SESSION_HISTORY(sessionId) + `?limit=${limit}`);
            if (response.ok) {
                const data = await response.json();
                return data.history || [];
            }

            return [];
        } catch (error) {
            console.error('Error getting history:', error);
            return [];
        }
    },

    /**
     * Update session context
     */
    async updateContext(contextData) {
        try {
            const sessionId = await this.getSessionId();
            if (!sessionId) return false;

            const response = await fetch(API_ENDPOINTS.SESSION_CONTEXT(sessionId), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context_data: contextData })
            });

            return response.ok;
        } catch (error) {
            console.error('Error updating context:', error);
            return false;
        }
    },

    /**
     * Clear current session
     */
    clearSession() {
        localStorage.removeItem(SESSION_STORAGE_KEY);
    }
};
