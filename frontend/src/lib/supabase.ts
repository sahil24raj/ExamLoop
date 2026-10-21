import { createClient, SupabaseClient, Session, User } from "@supabase/supabase-js";

const supabaseUrl = 
  process.env.NEXT_PUBLIC_SUPABASE_URL || 
  "https://evbcfypbwitqlkrsjsxf.supabase.co";

const supabaseAnonKey = 
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2YmNmeXBid2l0cWxrcnNqc3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxMjA3NjMsImV4cCI6MjEwMTY5Njc2M30.TUxqGUd0_vcOxdGovaDNrEJ9PJebajQthBSIddb2wPU";

export const isSupabaseConfigured = Boolean(
  supabaseUrl && 
  supabaseAnonKey && 
  !supabaseUrl.includes("your-project-ref") &&
  !supabaseAnonKey.includes("your-anon-key")
);

// Fallback dummy client if credentials aren't yet populated
export const supabase: SupabaseClient = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : createClient(
      supabaseUrl || "https://placeholder-project.supabase.co",
      supabaseAnonKey || "placeholder-anon-key",
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      }
    );

/**
 * Returns current access token if a Supabase session exists.
 */
export async function getSupabaseAccessToken(): Promise<string | null> {
  if (!isSupabaseConfigured) return null;
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  } catch (err) {
    console.error("Failed to get Supabase session token:", err);
    return null;
  }
}

/**
 * Returns current authenticated user or null.
 */
export async function getSupabaseUser(): Promise<User | null> {
  if (!isSupabaseConfigured) return null;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  } catch {
    return null;
  }
}
