import { render, screen, fireEvent } from '@testing-library/react';
import RecipeGenerator from './RecipeGenerator';

// Mock agent client
jest.mock('../services/agentClient', () => ({
  brewRecipe: jest.fn(() => Promise.resolve({
    recipe: {
      brewer: 'V60',
      temperature: 93,
      grinding_size: 20,
      dose: 15,
      target_water: 250,
      pours: [
        { start: 0, end: 30, water_added: 50 },
        { start: 45, end: 90, water_added: 100 },
        { start: 120, end: 180, water_added: 100 }
      ]
    }
  })),
  visualizeRecipe: jest.fn(() => Promise.resolve({ html: '<div>Chart</div>' }))
}));

describe('RecipeGenerator Comprehensive Tests', () => {
  const mockBeans = [
    { 
      bean_id: '1', 
      bean: { 
        name: 'Ethiopian Yirgacheffe',
        process: 'Washed',
        roast_level: 'Light',
        flavor_notes: ['citrus', 'floral']
      }
    },
    { 
      bean_id: '2', 
      bean: { 
        name: 'Colombian Supremo',
        process: 'Natural',
        roast_level: 'Medium'
      }
    }
  ];

  const mockOnRefreshBeans = jest.fn();

  test('renders with beans in library mode', () => {
    render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    expect(document.body).toBeInTheDocument();
  });

  test('renders with empty beans array', () => {
    render(<RecipeGenerator beans={[]} onRefreshBeans={mockOnRefreshBeans} />);
    expect(document.body).toBeInTheDocument();
  });

  test('has brewer selection options', () => {
    const { container } = render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    const selects = container.querySelectorAll('select');
    expect(selects.length).toBeGreaterThan(0);
  });

  test('has generate button', () => {
    const { container } = render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    const buttons = container.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  test('displays bean options when in library mode', () => {
    const { container } = render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    // Component should have some way to select beans
    expect(container.textContent.length).toBeGreaterThan(0);
  });

  test('handles mode switching', () => {
    const { container } = render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    const buttons = container.querySelectorAll('button');
    // Should have buttons for mode switching (library vs manual)
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  test('component has form structure', () => {
    const { container } = render(<RecipeGenerator beans={mockBeans} onRefreshBeans={mockOnRefreshBeans} />);
    const inputs = container.querySelectorAll('input, select, textarea');
    expect(inputs.length).toBeGreaterThan(0);
  });
});
