import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerManager, joinCompany, loginWithEmail } from '../api';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

type Mode = 'select' | 'manager' | 'employee' | 'login';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [mode, setMode] = useState<Mode>('select');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Manager form state
  const [managerEmail, setManagerEmail] = useState('');
  const [managerName, setManagerName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [companyDomain, setCompanyDomain] = useState('');

  // Employee form state
  const [employeeEmail, setEmployeeEmail] = useState('');
  const [employeeName, setEmployeeName] = useState('');
  const [inviteCode, setInviteCode] = useState('');

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');

  const handleManagerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await registerManager(
        managerEmail,
        managerName,
        companyName,
        companyDomain || undefined
      );
      login(data.user, data.company);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEmployeeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await joinCompany(employeeEmail, employeeName, inviteCode);
      login(data.user, data.company);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join company');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await loginWithEmail(loginEmail);
      login(data.user, data.company);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  if (mode === 'login') {
    return (
      <div className="login-page">
        <div className="login-container">
          <header className="login-header animate-fade-in">
            <button className="back-button" onClick={() => setMode('select')}>
              ← Back
            </button>
            <h1>Welcome Back</h1>
            <p className="subtitle">Sign in with your email</p>
          </header>

          <form onSubmit={handleLoginSubmit} className="login-form animate-fade-in stagger-1">
            <div className="form-group">
              <label htmlFor="loginEmail">Email</label>
              <input
                id="loginEmail"
                type="email"
                placeholder="you@company.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="btn btn-primary submit-btn" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (mode === 'select') {
    return (
      <div className="login-page">
        <div className="login-container">
          <header className="login-header animate-fade-in">
            <h1>Leveling Guide Generator</h1>
            <p className="subtitle">Help your team understand what great looks like</p>
          </header>

          <div className="role-selection animate-fade-in stagger-1">
            <button
              className="role-card"
              onClick={() => setMode('manager')}
            >
              <span className="role-icon">👔</span>
              <h3>I'm a Manager</h3>
              <p>Create a company and upload leveling guides for your team</p>
            </button>

            <button
              className="role-card"
              onClick={() => setMode('employee')}
            >
              <span className="role-icon">👤</span>
              <h3>I'm an Employee</h3>
              <p>Join your company to view leveling guides and request new ones</p>
            </button>
          </div>

          <div className="login-link animate-fade-in stagger-2">
            <p>Already have an account?</p>
            <button className="btn btn-secondary" onClick={() => setMode('login')}>
              Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'manager') {
    return (
      <div className="login-page">
        <div className="login-container">
          <header className="login-header animate-fade-in">
            <button className="back-button" onClick={() => setMode('select')}>
              ← Back
            </button>
            <h1>Create Your Company</h1>
            <p className="subtitle">Set up your organization and start creating leveling guides</p>
          </header>

          <form onSubmit={handleManagerSubmit} className="login-form animate-fade-in stagger-1">
            <div className="form-group">
              <label htmlFor="managerName">Your Name</label>
              <input
                id="managerName"
                type="text"
                placeholder="Jane Smith"
                value={managerName}
                onChange={(e) => setManagerName(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="managerEmail">Your Email</label>
              <input
                id="managerEmail"
                type="email"
                placeholder="jane@company.com"
                value={managerEmail}
                onChange={(e) => setManagerEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="companyName">Company Name</label>
              <input
                id="companyName"
                type="text"
                placeholder="Acme Inc."
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="companyDomain">Company Website (optional)</label>
              <input
                id="companyDomain"
                type="text"
                placeholder="acme.com"
                value={companyDomain}
                onChange={(e) => setCompanyDomain(e.target.value)}
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="btn btn-primary submit-btn" disabled={loading}>
              {loading ? 'Creating...' : 'Create Company'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Employee mode
  return (
    <div className="login-page">
      <div className="login-container">
        <header className="login-header animate-fade-in">
          <button className="back-button" onClick={() => setMode('select')}>
            ← Back
          </button>
          <h1>Join Your Company</h1>
          <p className="subtitle">Enter the invite code from your manager</p>
        </header>

        <form onSubmit={handleEmployeeSubmit} className="login-form animate-fade-in stagger-1">
          <div className="form-group">
            <label htmlFor="employeeName">Your Name</label>
            <input
              id="employeeName"
              type="text"
              placeholder="John Doe"
              value={employeeName}
              onChange={(e) => setEmployeeName(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="employeeEmail">Your Email</label>
            <input
              id="employeeEmail"
              type="email"
              placeholder="john@company.com"
              value={employeeEmail}
              onChange={(e) => setEmployeeEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="inviteCode">Invite Code</label>
            <input
              id="inviteCode"
              type="text"
              placeholder="ABC123XY"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              required
              disabled={loading}
              className="invite-code-input"
            />
            <span className="form-hint">Get this from your manager</span>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn btn-primary submit-btn" disabled={loading}>
            {loading ? 'Joining...' : 'Join Company'}
          </button>
        </form>
      </div>
    </div>
  );
}
