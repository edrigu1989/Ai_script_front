// src/lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

// src/lib/supabase/server.ts
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value, ...options })
          } catch (error) {
            // Handle error in Server Component
          }
        },
        remove(name: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value: '', ...options })
          } catch (error) {
            // Handle error in Server Component
          }
        },
      },
    }
  )
}

// src/lib/api/client.ts
import axios from 'axios'
import { createClient } from '@/lib/supabase/client'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  
  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.refreshSession()
      
      if (session) {
        // Retry the request with new token
        error.config.headers.Authorization = `Bearer ${session.access_token}`
        return api(error.config)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api

// src/lib/api/scripts.ts
import api from './client'
import { Script, ScriptGeneration } from '@/types'

export const scriptsApi = {
  generate: async (data: ScriptGeneration) => {
    const response = await api.post<Script>('/scripts/generate', data)
    return response.data
  },
  
  list: async (skip = 0, limit = 10) => {
    const response = await api.get<Script[]>('/scripts', {
      params: { skip, limit }
    })
    return response.data
  },
  
  get: async (id: string) => {
    const response = await api.get<Script>(`/scripts/${id}`)
    return response.data
  },
  
  regenerate: async (id: string, element: string, instructions?: string) => {
    const response = await api.post<Script>(`/scripts/${id}/regenerate`, {
      element,
      additional_instructions: instructions
    })
    return response.data
  }
}

// src/lib/stripe.ts
import { loadStripe } from '@stripe/stripe-js'

export const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!
)

// src/types/index.ts
export interface User {
  id: string
  email: string
  full_name?: string
  subscription_plan: 'free' | 'creator'
  subscription_status: 'active' | 'cancelled' | 'expired'
  onboarding_completed: boolean
  content_style?: string
  target_audience?: string
}

export interface Script {
  id: string
  user_id: string
  title: string
  content: string
  hook: string
  call_to_action: string
  tone: string
  duration: string
  platform: string
  metadata: {
    idea: string
    additional_context?: string
  }
  created_at: string
  updated_at: string
}

export interface ScriptGeneration {
  idea: string
  tone: 'casual' | 'professional' | 'humorous' | 'educational' | 'dramatic'
  duration: '30s' | '60s' | '90s' | '3min'
  platform: 'youtube' | 'tiktok' | 'instagram' | 'linkedin'
  additional_context?: string
}

export interface VideoAnalysis {
  id: string
  user_id: string
  video_url: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  results?: {
    technical: any
    qualitative: any
    recommendations: string[]
  }
  error?: string
  created_at: string
  updated_at: string
}

// src/lib/hooks/useUser.ts
import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { User } from '@/types'
import api from '@/lib/api/client'

export function useUser() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const supabase = createClient()
    
    const fetchUser = async () => {
      try {
        const { data: { user: authUser } } = await supabase.auth.getUser()
        
        if (authUser) {
          // Fetch full profile from our API
          const response = await api.get<User>(`/profiles/${authUser.id}`)
          setUser(response.data)
        }
      } catch (error) {
        console.error('Error fetching user:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchUser()
    
    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          const response = await api.get<User>(`/profiles/${session.user.id}`)
          setUser(response.data)
        } else if (event === 'SIGNED_OUT') {
          setUser(null)
        }
      }
    )
    
    return () => subscription.unsubscribe()
  }, [])
  
  return { user, loading }
}

// src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date) {
  return new Intl.DateTimeFormat('es-ES', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(date))
}

export function formatDuration(duration: string) {
  const map: Record<string, string> = {
    '30s': '30 segundos',
    '60s': '1 minuto',
    '90s': '1:30 minutos',
    '3min': '3 minutos',
  }
  return map[duration] || duration
}

// src/components/ui/button.tsx
import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-purple-600 text-white hover:bg-purple-700',
      secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
      ghost: 'bg-transparent hover:bg-gray-100',
      danger: 'bg-red-600 text-white hover:bg-red-700',
    }
    
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2',
      lg: 'px-6 py-3 text-lg',
    }
    
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }

// src/app/layout.tsx
import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Script Strategist - Crea contenido viral con IA',
  description: 'Genera guiones únicos y estratégicos para tus videos con inteligencia artificial',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        {children}
        <Toaster position="bottom-right" />
      </body>
    </html>
  )
}

// src/app/page.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Sparkles, Zap, Video, TrendingUp } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
        
        <nav className="relative z-10 flex items-center justify-between p-6 lg:px-8">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-8 w-8 text-purple-400" />
            <span className="text-2xl font-bold text-white">AI Script Strategist</span>
          </div>
          
          <div className="flex items-center space-x-6">
            <Link href="/login" className="text-white hover:text-purple-300 transition">
              Iniciar sesión
            </Link>
            <Link href="/signup">
              <Button>Empezar gratis</Button>
            </Link>
          </div>
        </nav>

        <div className="relative z-10 mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              Crea contenido <span className="text-purple-400">viral</span> con IA
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-300">
              Genera guiones únicos y estratégicos para tus videos. 
              Nuestra IA aprende de tu estilo y te ayuda a destacar en cualquier plataforma.
            </p>
            
            <div className="mt-10 flex gap-4 justify-center">
              <Link href="/signup">
                <Button size="lg" className="gap-2">
                  Probar gratis
                  <Sparkles className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          <div className="mx-auto mt-32 max-w-7xl grid grid-cols-1 gap-8 sm:grid-cols-3">
            <FeatureCard
              icon={<Zap />}
              title="Generación instantánea"
              description="Crea guiones completos en segundos con hooks virales y CTAs efectivos"
            />
            <FeatureCard
              icon={<Video />}
              title="Análisis de video"
              description="Sube tus videos y recibe feedback detallado para mejorar tu contenido"
            />
            <FeatureCard
              icon={<TrendingUp />}
              title="Radar de tendencias"
              description="Mantente al día con las tendencias virales de cada plataforma"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: any) {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-sm">
      <div className="mb-4 inline-flex rounded-lg bg-purple-500/10 p-3 text-purple-400">
        {icon}
      </div>
      <h3 className="mb-2 text-xl font-semibold text-white">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </div>
  )
}