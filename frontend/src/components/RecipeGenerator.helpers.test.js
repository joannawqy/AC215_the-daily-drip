import React from 'react';
import { render, screen } from '@testing-library/react';
import {
  BeanSummary,
  RatioBadge,
  buildManualPayload,
  computeRoastedDays,
  formatPourStep,
  stripBeanMetadata,
} from './RecipeGenerator';

describe('RecipeGenerator helper exports', () => {
  beforeAll(() => {
    jest.useFakeTimers().setSystemTime(new Date('2024-06-20T00:00:00Z'));
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  test('computeRoastedDays handles invalid and future dates', () => {
    expect(computeRoastedDays('2024-06-18')).toBe(2);
    expect(computeRoastedDays('invalid')).toBeNull();
    expect(computeRoastedDays('2024-06-30')).toBe(0);
  });

  test('buildManualPayload normalizes fields', () => {
    const payload = buildManualPayload({
      name: '  Kenya  ',
      origin: '  Nyeri ',
      process: ' Washed ',
      variety: '',
      roast_level: '3',
      altitude: '1800',
      flavor_notes: 'berry, citrus, ',
      roasted_on: '2024-06-18',
    });

    expect(payload.name).toBe('Kenya');
    expect(payload.origin).toBe('Nyeri');
    expect(payload.roast_level).toBe(3);
    expect(payload.altitude).toBe(1800);
    expect(payload.flavor_notes).toEqual(['berry', 'citrus']);
    expect(payload.roasted_days).toBe(2);
  });

  test('stripBeanMetadata removes internal identifiers', () => {
    const bean = {
      bean_id: 'b1',
      created_at: '2024-06-01',
      updated_at: '2024-06-02',
      name: 'Colombia',
    };
    expect(stripBeanMetadata(bean)).toEqual({ name: 'Colombia' });
  });

  test('formatPourStep renders pour information', () => {
    render(<div>{formatPourStep({ start: 0, end: 30, water_added: 60 }, 0)}</div>);
    expect(screen.getByText(/0s → 30s/)).toBeInTheDocument();
    expect(screen.getByText(/60g/)).toBeInTheDocument();
  });

  test('RatioBadge renders brew ratio', () => {
    render(<RatioBadge dose={16} water={256} />);
    expect(screen.getByText(/Ratio 1:16.0/)).toBeInTheDocument();
  });

  test('BeanSummary renders fallback values', () => {
    render(<BeanSummary bean={{ origin: '', process: '', flavor_notes: [] }} />);
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
