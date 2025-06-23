# 🚀 GUÍA COMPLETA: Frontend en Vercel para AI Script Strategist

## 1. Crear el proyecto Next.js
npx create-next-app@latest ai-script-frontend --typescript --tailwind --app
cd ai-script-frontend

## 2. Instalar todas las dependencias necesarias
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs @supabase/auth-ui-react @supabase/auth-ui-shared
npm install @stripe/stripe-js react-stripe-js
npm install axios swr zustand
npm install framer-motion
npm install react-hot-toast sonner
npm install @headlessui/react @heroicons/react
npm install react-hook-form zod @hookform/resolvers
npm install lucide-react
npm install clsx tailwind-merge
npm install react-markdown remark-gfm
npm install @tanstack/react-query
npm install date-fns

## 3. Configurar variables de entorno
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app

## 4. Estructura de carpetas optimizada
mkdir -p src/app/(auth)/{login,signup,forgot-password}
mkdir -p src/app/(dashboard)/{dashboard,scripts,analytics,settings,billing}
mkdir -p src/app/api/{auth,webhook}
mkdir -p src/components/{ui,auth,scripts,dashboard,landing}
mkdir -p src/lib/{api,hooks,store,utils}
mkdir -p src/types

## 5. Configuración de Vercel (vercel.json)
{
  "functions": {
    "src/app/api/webhook/stripe/route.ts": {
      "maxDuration": 30
    }
  },
  "redirects": [
    {
      "source": "/",
      "has": [
        {
          "type": "cookie",
          "key": "supabase-auth-token"
        }
      ],
      "destination": "/dashboard",
      "permanent": false
    }
  ]
}

## 6. Configurar Tailwind CSS (tailwind.config.ts)
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
export default config

## 7. Instalar Vercel CLI y hacer login
npm i -g vercel
vercel login

## 8. Desplegar en Vercel (método CLI)
vercel

# Te preguntará:
# - Set up and deploy? Y
# - Which scope? (selecciona tu cuenta)
# - Link to existing project? N
# - Project name? ai-script-strategist
# - Directory? ./
# - Want to override settings? N

## 9. Configurar variables de entorno en Vercel
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

## 10. Despliegue de producción
vercel --prod

## ALTERNATIVA: Desplegar con GitHub

# 1. Subir código a GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/ai-script-frontend.git
git push -u origin main

# 2. En vercel.app:
# - New Project
# - Import Git Repository
# - Seleccionar tu repo
# - Configurar variables de entorno
# - Deploy

## 11. Configurar dominio personalizado (opcional)
# En el dashboard de Vercel:
# Settings > Domains > Add
# Ejemplo: app.tuscript.ai

## 12. Scripts útiles en package.json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "preview": "next build && next start",
    "vercel-build": "prisma generate && next build",
    "postinstall": "prisma generate"
  }
}

## 13. Middleware para proteger rutas (src/middleware.ts)
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Proteger rutas del dashboard
  if (req.nextUrl.pathname.startsWith('/dashboard') && !user) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // Redirigir si ya está autenticado
  if (
    (req.nextUrl.pathname === '/login' || 
     req.nextUrl.pathname === '/signup') && 
    user
  ) {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  return res
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/signup']
}

## 14. Configuración de Next.js (next.config.js)
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'your-supabase-project.supabase.co',
      'lh3.googleusercontent.com', // Google profile images
    ],
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ]
  },
}

module.exports = nextConfig

## 15. GitHub Actions para CI/CD (opcional)
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}

## 16. Monitoreo y Analytics
# Vercel Analytics (automático)
npm install @vercel/analytics
npm install @vercel/speed-insights

# En app/layout.tsx:
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}

## 🎯 Comandos Rápidos

# Desarrollo local
npm run dev

# Preview de producción
npm run preview

# Desplegar a preview
vercel

# Desplegar a producción
vercel --prod

# Ver logs
vercel logs

# Gestionar secretos
vercel env ls
vercel env add KEY_NAME
vercel env rm KEY_NAME

# Rollback
vercel rollback

## 🔧 Optimizaciones Recomendadas

1. **Image Optimization**: Usa next/image para todas las imágenes
2. **Font Optimization**: Usa next/font para cargar fuentes
3. **API Routes**: Usa Route Handlers para APIs internas
4. **ISR**: Implementa Incremental Static Regeneration donde sea posible
5. **Edge Functions**: Usa Edge Runtime para funciones críticas

## 📊 Panel de Vercel

Accede a: https://vercel.com/dashboard

- Monitoreo en tiempo real
- Analytics de Web Vitals
- Logs de funciones
- Preview deployments
- Gestión de dominios
- Variables de entorno
- Integraciones (GitHub, Slack, etc.)

## 🚨 Troubleshooting Común

# Error: Module not found
rm -rf node_modules package-lock.json
npm install
vercel --prod --force

# Error: Environment variables
vercel env pull .env.local

# Error: Build failed
vercel logs
npm run build -- --debug

# Limpiar caché
vercel --prod --force

¡Tu frontend está listo para desplegarse en Vercel! 🚀