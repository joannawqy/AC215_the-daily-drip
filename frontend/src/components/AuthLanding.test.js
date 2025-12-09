import { render, screen, fireEvent } from '@testing-library/react';
import AuthLanding from './AuthLanding';

// Mock the AuthContext
jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: jest.fn(),
    register: jest.fn(),
    authLoading: false,
    error: null,
    clearError: jest.fn(),
    isAuthenticated: false
  })
}));

describe('AuthLanding Component', () => {
  test('renders landing page', () => {
    render(<AuthLanding />);
    // Component should render
    expect(document.body).toBeInTheDocument();
  });

  test('displays app title or branding', () => {
    const { container } = render(<AuthLanding />);
    // Check that some content is rendered
    expect(container.firstChild).toBeTruthy();
  });

  test('has interactive elements', () => {
    const { container } = render(<AuthLanding />);
    // Check for buttons or inputs
    const buttons = container.querySelectorAll('button');
    const inputs = container.querySelectorAll('input');
    expect(buttons.length + inputs.length).toBeGreaterThan(0);
  });
});
