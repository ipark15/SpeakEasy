import { createClient } from "@supabase/supabase-js"

const url = import.meta.env.VITE_SUPABASE_URL ?? "http://localhost"
const key = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "placeholder"

export const supabase = createClient(url, key)
