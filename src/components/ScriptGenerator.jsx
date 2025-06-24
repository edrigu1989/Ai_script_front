import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Sparkles, 
  Video, 
  Clock,
  Users,
  Target,
  Wand2,
  Copy,
  Download,
  Edit,
  Save,
  Loader2,
  ArrowLeft,
  Play
} from 'lucide-react'

const API_BASE_URL = 'https://aiscriptback-production.up.railway.app'

function ScriptGenerator({ user, onBack }) {
  const [formData, setFormData] = useState({
    topic: '',
    platform: 'youtube',
    duration: '60',
    audience: '',
    tone: 'engaging',
    style: 'educational'
  })
  
  const [generatedScript, setGeneratedScript] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')

  const platforms = [
    { value: 'youtube', label: 'YouTube', icon: '📺' },
    { value: 'tiktok', label: 'TikTok', icon: '🎵' },
    { value: 'instagram', label: 'Instagram', icon: '📸' },
    { value: 'linkedin', label: 'LinkedIn', icon: '💼' }
  ]

  const durations = [
    { value: '30', label: '30 seconds' },
    { value: '60', label: '1 minute' },
    { value: '90', label: '90 seconds' },
    { value: '180', label: '3 minutes' }
  ]

  const tones = [
    { value: 'engaging', label: 'Engaging' },
    { value: 'professional', label: 'Professional' },
    { value: 'casual', label: 'Casual' },
    { value: 'humorous', label: 'Humorous' },
    { value: 'inspirational', label: 'Inspirational' }
  ]

  const styles = [
    { value: 'educational', label: 'Educational' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'promotional', label: 'Promotional' },
    { value: 'storytelling', label: 'Storytelling' },
    { value: 'tutorial', label: 'Tutorial' }
  ]

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const generateScript = async () => {
    if (!formData.topic.trim()) {
      setError('Please enter a topic for your video')
      return
    }

    setIsGenerating(true)
    setError('')
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/scripts/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: user.email,
          topic: formData.topic,
          platform: formData.platform,
          duration: parseInt(formData.duration),
          audience: formData.audience,
          tone: formData.tone,
          style: formData.style
        })
      })

      const result = await response.json()
      
      if (!response.ok) {
        throw new Error(result.detail || 'Failed to generate script')
      }
      
      setGeneratedScript(result.script)
    } catch (error) {
      setError(error.message)
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedScript)
    // You could add a toast notification here
  }

  const downloadScript = () => {
    const blob = new Blob([generatedScript], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `script-${formData.platform}-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (generatedScript) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button variant="outline" onClick={() => setGeneratedScript('')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Generate New Script
            </Button>
            <div>
              <h2 className="text-2xl font-bold">Generated Script</h2>
              <p className="text-muted-foreground">
                {platforms.find(p => p.value === formData.platform)?.label} • {formData.duration}s • {formData.tone}
              </p>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={copyToClipboard}>
              <Copy className="h-4 w-4 mr-2" />
              Copy
            </Button>
            <Button variant="outline" onClick={downloadScript}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Video className="h-5 w-5" />
              <span>Your Video Script</span>
            </CardTitle>
            <CardDescription>
              Topic: {formData.topic}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted/30 p-6 rounded-lg">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                {generatedScript}
              </pre>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Button>
          <div>
            <h2 className="text-2xl font-bold">Create Video Script</h2>
            <p className="text-muted-foreground">Generate engaging scripts with AI</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Wand2 className="h-5 w-5" />
                <span>Script Parameters</span>
              </CardTitle>
              <CardDescription>
                Customize your video script with these parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Topic */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Video Topic *</label>
                <textarea
                  placeholder="Describe what your video is about..."
                  className="w-full p-3 border border-border rounded-md bg-background resize-none"
                  rows={3}
                  value={formData.topic}
                  onChange={(e) => handleInputChange('topic', e.target.value)}
                />
              </div>

              {/* Platform */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Platform</label>
                <div className="grid grid-cols-2 gap-2">
                  {platforms.map((platform) => (
                    <button
                      key={platform.value}
                      onClick={() => handleInputChange('platform', platform.value)}
                      className={`p-3 border rounded-md text-left transition-colors ${
                        formData.platform === platform.value
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{platform.icon}</span>
                        <span className="font-medium">{platform.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Duration</label>
                <div className="grid grid-cols-2 gap-2">
                  {durations.map((duration) => (
                    <button
                      key={duration.value}
                      onClick={() => handleInputChange('duration', duration.value)}
                      className={`p-3 border rounded-md text-center transition-colors ${
                        formData.duration === duration.value
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <Clock className="h-4 w-4 mx-auto mb-1" />
                      <span className="text-sm font-medium">{duration.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Audience */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Target Audience</label>
                <input
                  type="text"
                  placeholder="e.g., Young professionals, Tech enthusiasts, Parents..."
                  className="w-full p-3 border border-border rounded-md bg-background"
                  value={formData.audience}
                  onChange={(e) => handleInputChange('audience', e.target.value)}
                />
              </div>

              {/* Tone */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Tone</label>
                <select
                  className="w-full p-3 border border-border rounded-md bg-background"
                  value={formData.tone}
                  onChange={(e) => handleInputChange('tone', e.target.value)}
                >
                  {tones.map((tone) => (
                    <option key={tone.value} value={tone.value}>
                      {tone.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Style */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Content Style</label>
                <select
                  className="w-full p-3 border border-border rounded-md bg-background"
                  value={formData.style}
                  onChange={(e) => handleInputChange('style', e.target.value)}
                >
                  {styles.map((style) => (
                    <option key={style.value} value={style.value}>
                      {style.label}
                    </option>
                  ))}
                </select>
              </div>

              <Button 
                onClick={generateScript} 
                disabled={isGenerating || !formData.topic.trim()}
                className="w-full"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating Script...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Script
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Preview/Tips */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Tips</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium">For better results:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Be specific about your topic</li>
                  <li>• Define your target audience</li>
                  <li>• Choose the right platform</li>
                  <li>• Consider your video's purpose</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>Current Selection</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Platform:</span>
                <Badge variant="secondary">
                  {platforms.find(p => p.value === formData.platform)?.label}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Duration:</span>
                <Badge variant="secondary">
                  {durations.find(d => d.value === formData.duration)?.label}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Tone:</span>
                <Badge variant="secondary">
                  {tones.find(t => t.value === formData.tone)?.label}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Style:</span>
                <Badge variant="secondary">
                  {styles.find(s => s.value === formData.style)?.label}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ScriptGenerator

