import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Company, getMe } from '../api';

interface AuthState {
  user: User | null;
  company: Company | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (user: User, company: Company) => void;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    company: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const login = (user: User, company: Company) => {
    localStorage.setItem('userId', user.id);
    setState({
      user,
      company,
      isLoading: false,
      isAuthenticated: true,
    });
  };

  const logout = () => {
    localStorage.removeItem('userId');
    setState({
      user: null,
      company: null,
      isLoading: false,
      isAuthenticated: false,
    });
  };

  const refreshAuth = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    try {
      const data = await getMe();
      setState({
        user: data.user,
        company: data.company,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch {
      localStorage.removeItem('userId');
      setState({
        user: null,
        company: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  };

  useEffect(() => {
    refreshAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
