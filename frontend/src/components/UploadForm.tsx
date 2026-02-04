import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { createRole, waitForRole, checkRoleExists } from '../api';
import { useAuth } from '../context/AuthContext';
import './UploadForm.css';

type Status = 'idle' | 'uploading' | 'processing' | 'error';

export default function UploadForm() {
  const navigate = useNavigate();
  const { company } = useAuth();
  const [companyUrl, setCompanyUrl] = useState(company?.domain ? `https://${company.domain}` : '');
  const [roleName, setRoleName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);

  // Overwrite confirmation state
  const [showConfirmOverwrite, setShowConfirmOverwrite] = useState(false);
  const [existingRoleDate, setExistingRoleDate] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024, // 25MB
  });

  const doUpload = async () => {
    setShowConfirmOverwrite(false);
    setStatus('uploading');
    setError(null);

    try {
      const role = await createRole(file!, companyUrl, roleName);
      setStatus('processing');

      const completedRole = await waitForRole(role.id, (newStatus) => {
        console.log('Role status:', newStatus);
      });

      navigate(`/role/${completedRole.id}`);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !companyUrl || !roleName) {
      setError('Please fill in all fields and upload a file');
      return;
    }

    // Check if role already exists
    try {
      const check = await checkRoleExists(roleName);
      if (check.exists) {
        setExistingRoleDate(check.created_at);
        setShowConfirmOverwrite(true);
        return; // Wait for user confirmation
      }
    } catch (err) {
      // Continue anyway if check fails
      console.warn('Could not check for existing role:', err);
    }

    await doUpload();
  };

  const isLoading = status === 'uploading' || status === 'processing';

  return (
    <div className="upload-page">
      <div className="upload-container">
        <header className="upload-header animate-fade-in">
          <Link to="/dashboard" className="back-link">← Back to Dashboard</Link>
          <h1>Upload Leveling Guide</h1>
          <p className="subtitle">
            Transform your leveling guide into specific, actionable examples for your team
          </p>
        </header>

        <form onSubmit={handleSubmit} className="upload-form animate-fade-in stagger-1">
          <div className="form-group">
            <label htmlFor="companyUrl">Company Website</label>
            <input
              id="companyUrl"
              type="url"
              placeholder="https://yourcompany.com"
              value={companyUrl}
              onChange={(e) => setCompanyUrl(e.target.value)}
              disabled={isLoading}
              required
            />
            <span className="form-hint">Used for context when generating examples</span>
          </div>

          <div className="form-group">
            <label htmlFor="roleName">Role Name</label>
            <input
              id="roleName"
              type="text"
              placeholder="e.g., Software Engineer, Product Manager"
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="form-group">
            <label>Leveling Guide File</label>
            <div
              {...getRootProps()}
              className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${file ? 'dropzone-filled' : ''}`}
            >
              <input {...getInputProps()} disabled={isLoading} />
              {file ? (
                <div className="dropzone-file">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
              ) : isDragActive ? (
                <p>Drop your file here...</p>
              ) : (
                <div className="dropzone-empty">
                  <span className="upload-icon">⬆️</span>
                  <p>Drag & drop your leveling guide here</p>
                  <span className="dropzone-hint">PDF, CSV, TXT, or MD (max 5MB)</span>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {showConfirmOverwrite && (
            <div className="confirm-overwrite">
              <p>
                <strong>⚠️ A leveling guide for "{roleName}" already exists</strong>
              </p>
              <p>
                Created on {existingRoleDate ? new Date(existingRoleDate).toLocaleDateString() : 'a previous date'}.
                Uploading will replace the existing guide with this new one.
              </p>
              <div className="confirm-actions">
                <button type="button" className="btn btn-primary" onClick={doUpload}>
                  Yes, Replace It
                </button>
                <button 
                  type="button" 
                  className="btn btn-muted" 
                  onClick={() => setShowConfirmOverwrite(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary submit-btn"
            disabled={isLoading || !file || !companyUrl || !roleName || showConfirmOverwrite}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                {status === 'uploading' ? 'Uploading...' : 'Generating examples...'}
              </>
            ) : (
              'Generate Examples'
            )}
          </button>

          {status === 'processing' && (
            <p className="processing-hint">
              This may take a minute. We're generating 3 examples for each cell in your guide.
            </p>
          )}
        </form>

        <footer className="upload-footer animate-fade-in stagger-2">
          <p>
            Upload your company's leveling guide and get AI-generated examples
            that show employees exactly what great performance looks like at each level.
          </p>
        </footer>
      </div>
    </div>
  );
}
