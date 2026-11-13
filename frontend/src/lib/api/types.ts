export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_in: number;
  refresh_expires_in: number;
}

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_locked: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface Session {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_seen_at: string;
  is_active: boolean;
}

export interface MyPermissions {
  permissions: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string | null;
}
