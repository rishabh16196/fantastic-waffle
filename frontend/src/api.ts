/**
 * API client for the Leveling Guide Generator backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

// ==================== TYPES ====================

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'manager' | 'employee';
  company_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  domain: string | null;
  invite_code: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  company: Company;
}

export interface Nudge {
  id: string;
  employee_id: string;
  company_id: string;
  role_name: string;
  level_name: string | null;
  status: 'pending' | 'fulfilled' | 'dismissed';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  employee_name: string | null;
}

export interface Role {
  id: string;
  company_id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Level {
  id: string;
  company_id: string;
  role_id: string;
  name: string;
  order_idx: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Competency {
  id: string;
  company_id: string;
  role_id: string;
  name: string;
  order_idx: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Example {
  id: string;
  company_id: string;
  role_id: string;
  level_id: string;
  competency_id: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DefinitionWithExamples {
  id: string;
  level_id: string;
  level_name: string;
  competency_id: string;
  competency_name: string;
  definition: string;
  examples: Example[];
}

export interface RoleDetail extends Role {
  levels: Level[];
  competencies: Competency[];
  definitions: DefinitionWithExamples[];
}

export interface ProcessingStatus {
  role_id: string;
  status: 'processing' | 'completed' | 'failed';
  message?: string;
}

// ==================== HELPERS ====================

function getAuthHeaders(): HeadersInit {
  const userId = localStorage.getItem('userId');
  return userId ? { 'X-User-ID': userId } : {};
}

// ==================== AUTH API ====================

export async function registerManager(
  email: string,
  name: string,
  companyName: string,
  companyDomain?: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/register-manager`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      name,
      company_name: companyName,
      company_domain: companyDomain,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

export async function joinCompany(
  email: string,
  name: string,
  inviteCode: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/join-company`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      name,
      invite_code: inviteCode,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to join company');
  }

  return response.json();
}

export async function loginWithEmail(email: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function getMe(): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Not authenticated');
  }

  return response.json();
}

// ==================== NUDGE API ====================

export async function createNudge(
  roleName: string,
  levelName?: string
): Promise<Nudge> {
  const response = await fetch(`${API_BASE}/nudges`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({
      role_name: roleName,
      level_name: levelName,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create request');
  }

  return response.json();
}

export async function getNudges(): Promise<Nudge[]> {
  const response = await fetch(`${API_BASE}/nudges`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get requests');
  }

  return response.json();
}

export async function updateNudge(
  nudgeId: string,
  status: 'fulfilled' | 'dismissed'
): Promise<Nudge> {
  const response = await fetch(`${API_BASE}/nudges/${nudgeId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error('Failed to update request');
  }

  return response.json();
}

// ==================== ROLE API ====================

export interface RoleExistsCheck {
  exists: boolean;
  role_id: string | null;
  created_at: string | null;
}

export async function checkRoleExists(roleName: string): Promise<RoleExistsCheck> {
  const response = await fetch(
    `${API_BASE}/roles/check?role_name=${encodeURIComponent(roleName)}`,
    { headers: getAuthHeaders() }
  );

  if (!response.ok) {
    throw new Error('Failed to check role');
  }

  return response.json();
}

export async function createRole(
  file: File,
  companyUrl: string,
  roleName: string
): Promise<Role> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('company_url', companyUrl);
  formData.append('role_name', roleName);

  const response = await fetch(`${API_BASE}/roles`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create role');
  }

  return response.json();
}

export async function getRoleStatus(roleId: string): Promise<ProcessingStatus> {
  const response = await fetch(`${API_BASE}/roles/${roleId}/status`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get role status');
  }

  return response.json();
}

export async function getRole(roleId: string): Promise<RoleDetail> {
  const response = await fetch(`${API_BASE}/roles/${roleId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get role');
  }

  return response.json();
}

export async function getRoles(): Promise<Role[]> {
  const response = await fetch(`${API_BASE}/roles`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get roles');
  }

  return response.json();
}

export async function waitForRole(
  roleId: string,
  onStatusChange?: (status: string) => void,
  pollInterval = 2000
): Promise<RoleDetail> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getRoleStatus(roleId);
        onStatusChange?.(status.status);

        if (status.status === 'completed') {
          // Use the new role ID if provided (in case role was recreated)
          const finalRoleId = status.role_id || roleId;
          const role = await getRole(finalRoleId);
          resolve(role);
        } else if (status.status === 'failed') {
          reject(new Error(status.message || 'Role processing failed'));
        } else {
          setTimeout(poll, pollInterval);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}
