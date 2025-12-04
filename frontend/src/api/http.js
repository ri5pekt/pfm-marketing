// Use relative path in production (nginx will proxy /api to backend)
// Use environment variable or localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api')

function getAuthToken() {
  return localStorage.getItem('pfm_token')
}

export async function httpRequest(url, options = {}) {
  const token = getAuthToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const config = {
    ...options,
    headers
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
      const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      error.status = response.status // Attach status code to error
      throw error
    }

    return await response.json()
  } catch (error) {
    throw error
  }
}

export function get(url, options = {}) {
  return httpRequest(url, { ...options, method: 'GET' })
}

export function post(url, data, options = {}) {
  return httpRequest(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export function put(url, data, options = {}) {
  return httpRequest(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data)
  })
}

export function del(url, options = {}) {
  return httpRequest(url, { ...options, method: 'DELETE' })
}

