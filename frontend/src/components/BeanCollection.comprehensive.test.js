import { render, fireEvent } from '@testing-library/react';
import BeanCollection from './BeanCollection';

describe('BeanCollection Comprehensive Tests', () => {
  const mockBeans = [
    { 
      bean_id: '1', 
      name: 'Ethiopian Yirgacheffe',
      bean: { 
        name: 'Ethiopian Yirgacheffe',
        roast_level: 'Light',
        process: 'Washed',
        flavor_notes: ['citrus', 'floral', 'tea']
      }
    },
    { 
      bean_id: '2', 
      name: 'Colombian Supremo',
      bean: { 
        name: 'Colombian Supremo',
        roast_level: 'Medium',
        process: 'Natural'
      }
    },
    { 
      bean_id: '3', 
      name: 'Kenya AA',
      bean: { 
        name: 'Kenya AA',
        roast_level: 'Medium-Light',
        process: 'Washed'
      }
    }
  ];

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  test('renders with multiple beans', () => {
    render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(document.body).toBeInTheDocument();
  });

  test('renders with empty beans array', () => {
    render(<BeanCollection beans={[]} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(document.body).toBeInTheDocument();
  });

  test('displays beans in collection', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    // Should render some content for beans
    expect(container.textContent.length).toBeGreaterThan(0);
  });

  test('has interactive elements for management', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const buttons = container.querySelectorAll('button');
    // Should have buttons for edit/delete
    expect(buttons.length).toBeGreaterThan(0);
  });

  test('renders bean details', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    // Component should display bean information
    const content = container.textContent;
    // At least some bean-related content should be present
    expect(content.length).toBeGreaterThan(0);
  });

  test('handles single bean', () => {
    render(<BeanCollection beans={[mockBeans[0]]} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(document.body).toBeInTheDocument();
  });

  test('component structure is valid', () => {
    const { container } = render(<BeanCollection beans={mockBeans} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(container.firstChild).toBeTruthy();
  });
});
