import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
    // App should render successfully
    expect(document.body).toBeInTheDocument();
  });

  test('renders main application container', () => {
    const { container } = render(<App />);
    expect(container.firstChild).toBeTruthy();
  });
});
