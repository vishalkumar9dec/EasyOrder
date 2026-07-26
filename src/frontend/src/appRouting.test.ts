import { describe, expect, it } from 'vitest';

import { shouldObserveFadeUps } from './App';

describe('standalone route animations', () => {
  it('reveals the interactive controls on the playground route', () => {
    expect(shouldObserveFadeUps(false, false, false, true)).toBe(true);
  });
});
