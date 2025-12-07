const API_BASE_URL = process.env.REACT_APP_AGENT_API_URL || 'http://localhost:9000';

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function clearAuthToken() {
  authToken = null;
}

async function handleResponse(response) {
  const contentType = response.headers.get('content-type');
  let body;

  if (contentType && contentType.includes('application/json')) {
    body = await response.json();
  } else {
    body = await response.text();
  }

  if (!response.ok) {
    const detail = body?.detail || body?.message || body;
    throw new Error(typeof detail === 'string' ? detail : 'Request failed');
  }

  return body;
}

async function request(path, { method = 'GET', body, headers = {}, includeAuth = true } = {}) {
  const config = { method, headers: { ...headers } };

  if (body !== undefined) {
    config.headers['Content-Type'] = 'application/json';
    config.body = JSON.stringify(body);
  }

  if (includeAuth && authToken) {
    config.headers['X-Auth-Token'] = authToken;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, config);
  return handleResponse(response);
}

export function registerUser(payload) {
  return request('/auth/register', { method: 'POST', body: payload, includeAuth: false });
}

export function loginUser(payload) {
  return request('/auth/login', { method: 'POST', body: payload, includeAuth: false });
}

export function fetchProfile() {
  return request('/profile');
}

export function updatePreferences(payload) {
  return request('/profile/preferences', { method: 'PUT', body: payload });
}

export function listBeans() {
  return request('/beans');
}

export function createBean(payload) {
  return request('/beans', { method: 'POST', body: payload });
}

export function updateBean(beanId, payload) {
  return request(`/beans/${beanId}`, { method: 'PUT', body: payload });
}

export function deleteBean(beanId) {
  return request(`/beans/${beanId}`, { method: 'DELETE' });
}

export function brewRecipe(payload) {
  return request('/brew', { method: 'POST', body: payload });
}

export function visualizeRecipe(recipe, formats = ['html']) {
  return request('/visualize', { method: 'POST', body: { recipe, formats } });
}

export function submitFeedback(payload) {
  return request('/feedback', { method: 'POST', body: payload });
}
