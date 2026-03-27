export interface Profile {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  institution: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string | null;
}
