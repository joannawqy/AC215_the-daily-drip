import { brewRecipe, visualizeRecipe, listBeans, registerUser, loginUser } from './agentClient';

// Mock fetch globally
global.fetch = jest.fn();

describe('Agent Client Service', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('brewRecipe makes API call', async () => {
    const mockResponse = {
      recipe: { method: 'V60', grind_size: 'Medium-fine' }
    };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse
    });

    const payload = {
      bean: { name: 'Ethiopian Yirgacheffe' }
    };

    const result = await brewRecipe(payload);
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockResponse);
  });

  test('brewRecipe handles errors', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ detail: 'Error occurred' })
    });

    const payload = { bean: { name: 'Test Bean' } };

    await expect(brewRecipe(payload)).rejects.toThrow('Error occurred');
  });

  test('visualizeRecipe makes API call', async () => {
    const mockResponse = { html: '<div>Chart</div>' };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse
    });

    const recipe = { method: 'V60' };
    const result = await visualizeRecipe(recipe, ['html']);
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockResponse);
  });

  test('listBeans makes API call', async () => {
    const mockBeans = [
      { bean_id: '1', bean: { name: 'Ethiopian' } }
    ];
    
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockBeans
    });

    const result = await listBeans();
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockBeans);
  });

  test('registerUser makes API call', async () => {
    const mockResponse = { token: 'abc123' };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse
    });

    const userData = {
      email: 'test@example.com',
      password: 'password123'
    };

    const result = await registerUser(userData);
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockResponse);
  });

  test('loginUser makes API call', async () => {
    const mockResponse = { token: 'xyz789' };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse
    });

    const credentials = {
      email: 'test@example.com',
      password: 'password123'
    };

    const result = await loginUser(credentials);
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockResponse);
  });
});
