import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import RecipeGenerator from './RecipeGenerator';
import { brewRecipe, visualizeRecipe } from '../services/agentClient';

jest.mock('../services/agentClient', () => ({
  brewRecipe: jest.fn(),
  visualizeRecipe: jest.fn(),
}));

const mockBrewResult = {
  recipe: {
    brewing: {
      brewer: 'V60',
      temperature: 93,
      grinding_size: 22,
      dose: 16,
      target_water: 256,
      pours: [
        { start: 0, end: 30, water_added: 100 },
        { start: 30, end: 70, water_added: 156 },
      ],
    },
  },
  references: [{ rank: 1, id: 'ref-1', distance: 0.12, bean_text: 'Mock bean' }],
};

const mockVisualization = {
  outputs: { html: '<div>chart</div>', ascii: 'ASCII FLOW' },
  summary: { total_time: 90 },
};

describe('RecipeGenerator component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    brewRecipe.mockResolvedValue(mockBrewResult);
    visualizeRecipe.mockResolvedValue(mockVisualization);
  });

  test('shows validation message when manual bean lacks name', async () => {
    render(<RecipeGenerator beans={[]} onRefreshBeans={jest.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Generate recipe/i }));

    expect(await screen.findByText(/Bean name is required/)).toBeInTheDocument();
    expect(brewRecipe).not.toHaveBeenCalled();
  });
});
