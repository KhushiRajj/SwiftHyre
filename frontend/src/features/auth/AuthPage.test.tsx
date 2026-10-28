import { fireEvent, render, screen } from '@testing-library/react';
import AuthPage from './AuthPage';

describe('AuthPage', () => {
  it('shows validation errors for incomplete auth form', () => {
    render(<AuthPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Please complete all fields.');
  });
});
