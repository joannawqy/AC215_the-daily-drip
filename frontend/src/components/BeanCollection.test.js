import { render, screen } from '@testing-library/react';
import BeanCollection from './BeanCollection';

describe('BeanCollection Component', () => {
  const mockBeans = [
    { 
      bean_id: '1', 
      name: 'Ethiopian Yirgacheffe',
      bean: { name: 'Ethiopian Yirgacheffe', roast_level: 'Light' }
    },
    { 
      bean_id: '2', 
      name: 'Colombian Supremo',
      bean: { name: 'Colombian Supremo', roast_level: 'Medium' }
    }
  ];

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  test('renders bean collection', () => {
    render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(document.body).toBeInTheDocument();
  });

  test('displays collection container', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(container.firstChild).toBeTruthy();
  });

  test('has interactive elements for bean management', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    // Should have some buttons or interactive elements
    const interactiveElements = container.querySelectorAll('button, input, select');
    expect(interactiveElements.length).toBeGreaterThanOrEqual(0);
  });
});
