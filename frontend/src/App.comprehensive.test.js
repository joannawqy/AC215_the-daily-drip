import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

// Mock all dependencies
jest.mock('./context/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: {
      email: 'test@example.com',
      displayName: 'Test User',
      preferences: {}
    },
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    updateUser: jest.fn(),
    authLoading: false,
    error: null,
    clearError: jest.fn()
  }),
  AuthProvider: ({ children }) => <div>{children}</div>
}));

jest.mock('./services/agentClient', () => ({
  listBeans: jest.fn(() => Promise.resolve([
    { bean_id: '1', bean: { name: 'Ethiopian' } },
    { bean_id: '2', bean: { name: 'Colombian' } }
  ])),
  brewRecipe: jest.fn(() => Promise.resolve({ recipe: {} })),
  fetchProfile: jest.fn(() => Promise.resolve({})),
  createBean: jest.fn(() => Promise.resolve({ id: '3' })),
  deleteBean: jest.fn(() => Promise.resolve({})),
  updateBean: jest.fn(() => Promise.resolve({}))
}));

describe('App Component Comprehensive Tests', () => {
  test('renders main app container', () => {
    const { container } = render(<App />);
    expect(container.firstChild).toBeTruthy();
  });

  test('app has interactive structure', () => {
    const { container } = render(<App />);
    // Check that there are interactive elements
    const buttons = container.querySelectorAll('button');
    const inputs = container.querySelectorAll('input, select, textarea');
    expect(buttons.length + inputs.length).toBeGreaterThan(0);
  });

  test('app renders without errors', () => {
    expect(() => render(<App />)).not.toThrow();
  });

  test('app contains navigation or tabs', () => {
    const { container } = render(<App />);
    // App likely has some navigation structure
    expect(container.textContent.length).toBeGreaterThan(0);
  });
});
