import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the SwiftHyre heading', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'SwiftHyre' })).toBeInTheDocument();
  });
});
