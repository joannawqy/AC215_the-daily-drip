import React from 'react';
import { render } from '@testing-library/react';
import { AuthProvider } from './AuthContext';

// Mock the agent client
jest.mock('../services/agentClient', () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  fetchProfile: jest.fn(),
  setAuthToken: jest.fn(),
  clearAuthToken: jest.fn()
}));

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('AuthProvider renders children', () => {
    const { container } = render(
      <AuthProvider>
        <div>Test Child</div>
      </AuthProvider>
    );
    expect(container.textContent).toContain('Test Child');
  });

  test('AuthProvider renders without crashing', () => {
    const { container } = render(
      <AuthProvider>
        <div>Content</div>
      </AuthProvider>
    );
    expect(container).toBeTruthy();
  });
});
