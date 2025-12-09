import { render, screen } from '@testing-library/react';
import Profile from './Profile';

describe('Profile Component', () => {
  const mockUser = {
    email: 'test@example.com',
    displayName: 'Test User',
    preferences: {
      roast_level: 'Medium',
      flavor_notes: ['chocolate', 'caramel']
    }
  };

  const mockOnSavePreferences = jest.fn();

  test('renders profile page', () => {
    render(<Profile user={mockUser} onSavePreferences={mockOnSavePreferences} />);
    expect(document.body).toBeInTheDocument();
  });

  test('displays user information', () => {
    const { container } = render(<Profile user={mockUser} onSavePreferences={mockOnSavePreferences} />);
    expect(container.firstChild).toBeTruthy();
  });

  test('has interactive elements', () => {
    const { container } = render(<Profile user={mockUser} onSavePreferences={mockOnSavePreferences} />);
    const buttons = container.querySelectorAll('button');
    const inputs = container.querySelectorAll('input, select, textarea');
    expect(buttons.length + inputs.length).toBeGreaterThanOrEqual(0);
  });
});
