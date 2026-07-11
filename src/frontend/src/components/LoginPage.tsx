import { FormEvent, useState } from 'react';

import { isValidPhoneInput, requestOtp, verifyOtp } from '../accountModel';

export function LoginPage() {
  const [step, setStep] = useState<'phone' | 'code'>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handlePhoneSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!isValidPhoneInput(phone)) {
      setError('Enter your WhatsApp number with country code, e.g. +91 99887 76655');
      return;
    }
    setBusy(true);
    try {
      await requestOtp(phone);
      setStep('code');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send the code');
    } finally {
      setBusy(false);
    }
  }

  async function handleCodeSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await verifyOtp(phone, code);
      window.location.href = '/orders';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not verify the code');
      setBusy(false);
    }
  }

  return (
    <section className="account-page" aria-label="Log in to EasyOrder">
      <div className="account-card">
        <a className="navbar-brand account-brand" href="/">
          Easy<span>Order</span>
        </a>
        <h1 className="account-title">Log in with WhatsApp</h1>
        <p className="account-subtitle">
          {step === 'phone'
            ? 'We will send a one-time code to your WhatsApp.'
            : `Enter the 6-digit code sent to ${phone} on WhatsApp.`}
        </p>

        {step === 'phone' ? (
          <form onSubmit={handlePhoneSubmit} className="account-form" id="login-phone-form">
            <label className="account-label" htmlFor="login-phone">
              WhatsApp number
            </label>
            <input
              id="login-phone"
              className="account-input"
              type="tel"
              inputMode="tel"
              placeholder="+91 99887 76655"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              autoFocus
            />
            <button className="account-submit" type="submit" disabled={busy}>
              {busy ? 'Sending…' : 'Send code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleCodeSubmit} className="account-form" id="login-code-form">
            <label className="account-label" htmlFor="login-code">
              One-time code
            </label>
            <input
              id="login-code"
              className="account-input account-input--code"
              type="text"
              inputMode="numeric"
              pattern="\d{6}"
              maxLength={6}
              placeholder="••••••"
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
              autoFocus
            />
            <button className="account-submit" type="submit" disabled={busy || code.length !== 6}>
              {busy ? 'Verifying…' : 'Verify and log in'}
            </button>
            <button
              className="account-link-button"
              type="button"
              onClick={() => {
                setStep('phone');
                setCode('');
                setError(null);
              }}
            >
              Use a different number
            </button>
          </form>
        )}

        {error && (
          <p className="account-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </section>
  );
}
