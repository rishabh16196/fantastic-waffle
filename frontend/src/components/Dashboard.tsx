import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getRoles, getNudges, updateNudge, createNudge, Role, Nudge } from '../api';
import './Dashboard.css';

export default function Dashboard() {
  const { user, company, logout, isLoading } = useAuth();
  const navigate = useNavigate();
  const [roles, setRoles] = useState<Role[]>([]);
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Request form state (for employees)
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [requestRole, setRequestRole] = useState('');
  const [requestLevel, setRequestLevel] = useState('');
  const [submittingRequest, setSubmittingRequest] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/login');
    }
  }, [isLoading, user, navigate]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rolesData, nudgesData] = await Promise.all([
          getRoles(),
          getNudges(),
        ]);
        setRoles(rolesData);
        setNudges(nudgesData);
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setLoadingData(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNudgeAction = async (nudgeId: string, status: 'fulfilled' | 'dismissed') => {
    try {
      await updateNudge(nudgeId, status);
      setNudges(prev => prev.map(n => n.id === nudgeId ? { ...n, status } : n));
    } catch {
      setError('Failed to update request');
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingRequest(true);
    setError(null);

    try {
      const newNudge = await createNudge(requestRole, requestLevel || undefined);
      setNudges(prev => [newNudge, ...prev]);
      setShowRequestForm(false);
      setRequestRole('');
      setRequestLevel('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create request');
    } finally {
      setSubmittingRequest(false);
    }
  };

  if (isLoading || loadingData) {
    return (
      <div className="dashboard-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user || !company) {
    return null;
  }

  const isManager = user.role === 'manager';
  const pendingNudges = nudges.filter(n => n.status === 'pending');
  const activeRoles = roles.filter(r => r.is_active);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header animate-fade-in">
        <div className="header-left">
          <h1>{company.name}</h1>
          <span className="role-badge">{isManager ? 'Manager' : 'Employee'}</span>
        </div>
        <div className="header-right">
          <span className="user-name">{user.name}</span>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Manager: Show invite code */}
        {isManager && (
          <div className="invite-code-card animate-fade-in stagger-1">
            <h3>Invite Your Team</h3>
            <p>Share this code with employees so they can join:</p>
            <div className="invite-code">{company.invite_code}</div>
          </div>
        )}

        {/* Manager: Show nudge notifications */}
        {isManager && pendingNudges.length > 0 && (
          <div className="nudges-section animate-fade-in stagger-2">
            <h2>Guide Requests ({pendingNudges.length})</h2>
            <div className="nudges-list">
              {pendingNudges.map(nudge => (
                <div key={nudge.id} className="nudge-card">
                  <div className="nudge-info">
                    <strong>{nudge.employee_name}</strong> requested a guide for
                    <span className="nudge-role"> {nudge.role_name}</span>
                    {nudge.level_name && <span className="nudge-level"> ({nudge.level_name})</span>}
                  </div>
                  <div className="nudge-actions">
                    <button
                      onClick={() => handleNudgeAction(nudge.id, 'fulfilled')}
                      className="btn-small btn-success"
                    >
                      Mark Done
                    </button>
                    <button
                      onClick={() => handleNudgeAction(nudge.id, 'dismissed')}
                      className="btn-small btn-muted"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Manager: Upload new guide button */}
        {isManager && (
          <div className="actions-section animate-fade-in stagger-2">
            <Link to="/upload" className="btn btn-primary">
              + Upload New Leveling Guide
            </Link>
          </div>
        )}

        {/* Employee: Request a guide */}
        {!isManager && (
          <div className="request-section animate-fade-in stagger-1">
            {!showRequestForm ? (
              <button
                onClick={() => setShowRequestForm(true)}
                className="btn btn-secondary"
              >
                Request a Leveling Guide
              </button>
            ) : (
              <form onSubmit={handleCreateRequest} className="request-form">
                <h3>Request a Guide</h3>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="requestRole">Role</label>
                    <input
                      id="requestRole"
                      type="text"
                      placeholder="e.g., Software Engineer"
                      value={requestRole}
                      onChange={(e) => setRequestRole(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="requestLevel">Level (optional)</label>
                    <input
                      id="requestLevel"
                      type="text"
                      placeholder="e.g., L4"
                      value={requestLevel}
                      onChange={(e) => setRequestLevel(e.target.value)}
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={submittingRequest}>
                    {submittingRequest ? 'Sending...' : 'Send Request'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRequestForm(false)}
                    className="btn btn-muted"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {/* Leveling Guides List */}
        <div className="guides-section animate-fade-in stagger-3">
          <h2>Leveling Guides</h2>
          {activeRoles.length === 0 ? (
            <div className="empty-state">
              <p>No leveling guides yet.</p>
              {isManager && <p>Upload your first guide to get started!</p>}
              {!isManager && <p>Ask your manager to create one, or request a specific guide.</p>}
            </div>
          ) : (
            <div className="guides-grid">
              {activeRoles.map(role => (
                <Link
                  key={role.id}
                  to={`/role/${role.id}`}
                  className="guide-card"
                >
                  <h3>{role.name}</h3>
                  <p className="guide-date">
                    Created {new Date(role.created_at).toLocaleDateString()}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Employee: Show their requests */}
        {!isManager && nudges.length > 0 && (
          <div className="my-requests-section animate-fade-in stagger-4">
            <h2>Your Requests</h2>
            <div className="requests-list">
              {nudges.map(nudge => (
                <div key={nudge.id} className={`request-item status-${nudge.status}`}>
                  <span className="request-role">{nudge.role_name}</span>
                  {nudge.level_name && <span className="request-level">({nudge.level_name})</span>}
                  <span className={`status-badge ${nudge.status}`}>{nudge.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
