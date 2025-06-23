import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Sparkles, 
  Video, 
  Zap, 
  Users, 
  TrendingUp, 
  Clock,
  Star,
  ArrowRight,
  Play,
  CheckCircle,
  Sun,
  Moon,
  X,
  Mail,
  Lock,
  User
} from 'lucide-react'
import './App.css'

function App() {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ name: '', email: '', password: '' })

  // Initialize dark mode on component mount
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
    document.documentElement.classList.toggle('dark')
  }

  const handleLogin = (e) => {
    e.preventDefault()
    alert(`Login attempt with email: ${loginForm.email}`)
    setShowLoginModal(false)
    setLoginForm({ email: '', password: '' })
  }

  const handleRegister = (e) => {
    e.preventDefault()
    alert(`Registration attempt with name: ${registerForm.name}, email: ${registerForm.email}`)
    setShowRegisterModal(false)
    setRegisterForm({ name: '', email: '', password: '' })
  }

  const handleStartCreating = () => {
    alert('Redirecting to script creation tool...')
  }

  const handleWatchDemo = () => {
    alert('Opening demo video...')
  }

  const handleStartFreeTrial = () => {
    alert('Starting free trial...')
  }

  const handleViewPricing = () => {
    alert('Redirecting to pricing page...')
  }

  const features = [
    {
      icon: <Sparkles className="h-6 w-6" />,
      title: "AI-Powered Scripts",
      description: "Generate compelling video scripts using advanced AI technology tailored to your content style."
    },
    {
      icon: <Video className="h-6 w-6" />,
      title: "Multi-Platform Support",
      description: "Create scripts optimized for YouTube, TikTok, Instagram, and LinkedIn with platform-specific formats."
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: "Lightning Fast",
      description: "Generate professional scripts in seconds, not hours. Perfect for content creators on tight schedules."
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: "Audience Targeting",
      description: "Customize scripts based on your target audience demographics and interests."
    },
    {
      icon: <TrendingUp className="h-6 w-6" />,
      title: "Trend Analysis",
      description: "Leverage trending topics and viral content patterns to maximize engagement."
    },
    {
      icon: <Clock className="h-6 w-6" />,
      title: "Multiple Durations",
      description: "Generate scripts for 30s, 60s, 90s, or 3-minute videos based on your needs."
    }
  ]

  const testimonials = [
    {
      name: "Sarah Johnson",
      role: "YouTube Creator",
      content: "AI Script Strategist has revolutionized my content creation process. I can now produce engaging scripts in minutes!",
      rating: 5
    },
    {
      name: "Mike Chen",
      role: "TikTok Influencer",
      content: "The platform-specific optimization is incredible. My engagement rates have increased by 40% since using this tool.",
      rating: 5
    },
    {
      name: "Emma Davis",
      role: "Marketing Manager",
      content: "Perfect for our social media campaigns. The AI understands our brand voice and creates consistent, high-quality content.",
      rating: 5
    }
  ]

  return (
    <div className={`min-h-screen bg-background text-foreground ${isDarkMode ? 'dark' : ''}`}>
      {/* Header */}
      <header className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">AI Script Strategist</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={toggleDarkMode} className="p-2">
              {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button variant="outline" onClick={() => setShowLoginModal(true)}>
              Sign In
            </Button>
            <Button onClick={() => setShowRegisterModal(true)}>
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <Badge className="mb-4" variant="secondary">
            <Sparkles className="h-4 w-4 mr-1" />
            AI-Powered Content Creation
          </Badge>
          <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Generate Engaging Video Scripts
            <br />
            in Seconds
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Transform your ideas into compelling video scripts with our AI-powered platform. 
            Perfect for YouTube, TikTok, Instagram, and LinkedIn content creators.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" className="text-lg px-8" onClick={handleStartCreating}>
              <Play className="h-5 w-5 mr-2" />
              Start Creating
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8" onClick={handleWatchDemo}>
              Watch Demo
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold mb-4">Powerful Features</h3>
            <p className="text-xl text-muted-foreground">
              Everything you need to create engaging video content
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="border-border/50 bg-card/50 backdrop-blur hover:bg-card/70 transition-colors cursor-pointer">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold mb-4">What Creators Say</h3>
            <p className="text-xl text-muted-foreground">
              Join thousands of content creators who trust AI Script Strategist
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border-border/50 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-1 mb-2">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <CardDescription className="text-base italic">
                    "{testimonial.content}"
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div>
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary/5">
        <div className="container mx-auto text-center">
          <h3 className="text-3xl font-bold mb-4">Ready to Transform Your Content?</h3>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of content creators who are already using AI Script Strategist 
            to create engaging video content that drives results.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" className="text-lg px-8" onClick={handleStartFreeTrial}>
              <CheckCircle className="h-5 w-5 mr-2" />
              Start Free Trial
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8" onClick={handleViewPricing}>
              View Pricing
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-12 px-4">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">AI Script Strategist</span>
            </div>
            <p className="text-muted-foreground">
              © 2025 AI Script Strategist. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Sign In</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowLoginModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="email"
                      placeholder="Enter your email"
                      className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="password"
                      placeholder="Enter your password"
                      className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full">
                  Sign In
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => {
                      setShowLoginModal(false)
                      setShowRegisterModal(true)
                    }}
                  >
                    Sign up
                  </button>
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Get Started</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowRegisterModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Enter your full name"
                      className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background"
                      value={registerForm.name}
                      onChange={(e) => setRegisterForm({...registerForm, name: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="email"
                      placeholder="Enter your email"
                      className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      type="password"
                      placeholder="Create a password"
                      className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full">
                  Create Account
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => {
                      setShowRegisterModal(false)
                      setShowLoginModal(true)
                    }}
                  >
                    Sign in
                  </button>
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default App

