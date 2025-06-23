// supabase/functions/process-video/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.7.1'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface VideoUploadEvent {
  videoUrl: string
  analysisId: string
  userId: string
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    const { videoUrl, analysisId, userId } = await req.json() as VideoUploadEvent

    // Update status to processing
    await supabaseClient
      .from('video_analyses')
      .update({ 
        status: 'processing',
        updated_at: new Date().toISOString()
      })
      .eq('id', analysisId)

    // Call Google Video Intelligence API
    const googleApiKey = Deno.env.get('GOOGLE_API_KEY')
    const videoIntelligenceUrl = `https://videointelligence.googleapis.com/v1/videos:annotate?key=${googleApiKey}`
    
    const googleResponse = await fetch(videoIntelligenceUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        inputUri: videoUrl,
        features: ['LABEL_DETECTION', 'SHOT_CHANGE_DETECTION', 'SPEECH_TRANSCRIPTION'],
        videoContext: {
          speechTranscriptionConfig: {
            languageCode: 'es-ES',
            enableAutomaticPunctuation: true,
          }
        }
      })
    })

    if (!googleResponse.ok) {
      throw new Error(`Google API error: ${googleResponse.statusText}`)
    }

    const googleData = await googleResponse.json()
    const operationName = googleData.name

    // Poll for operation completion
    let operationComplete = false
    let analysisResults = null
    const maxAttempts = 60 // 5 minutes max
    let attempts = 0

    while (!operationComplete && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)) // Wait 5 seconds
      
      const statusResponse = await fetch(
        `https://videointelligence.googleapis.com/v1/${operationName}?key=${googleApiKey}`
      )
      
      const statusData = await statusResponse.json()
      
      if (statusData.done) {
        operationComplete = true
        analysisResults = statusData.response
      }
      
      attempts++
    }

    if (!analysisResults) {
      throw new Error('Video analysis timed out')
    }

    // Process results
    const processedResults = processVideoIntelligenceResults(analysisResults)

    // Call our backend API for qualitative analysis
    const backendUrl = Deno.env.get('BACKEND_URL') || 'https://your-app.railway.app'
    const qualitativeResponse = await fetch(`${backendUrl}/api/v1/videos/analyze-qualitative`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Service-Auth': Deno.env.get('SERVICE_AUTH_KEY') || ''
      },
      body: JSON.stringify({
        analysisId,
        technicalData: processedResults
      })
    })

    if (!qualitativeResponse.ok) {
      throw new Error('Qualitative analysis failed')
    }

    const qualitativeData = await qualitativeResponse.json()

    // Update analysis with final results
    await supabaseClient
      .from('video_analyses')
      .update({
        status: 'completed',
        results: {
          technical: processedResults,
          qualitative: qualitativeData,
          completedAt: new Date().toISOString()
        },
        updated_at: new Date().toISOString()
      })
      .eq('id', analysisId)

    return new Response(
      JSON.stringify({ success: true, analysisId }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    console.error('Error processing video:', error)
    
    // Update analysis with error
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )
    
    const { analysisId } = await req.json()
    
    await supabaseClient
      .from('video_analyses')
      .update({
        status: 'failed',
        error: error.message,
        updated_at: new Date().toISOString()
      })
      .eq('id', analysisId)

    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})

function processVideoIntelligenceResults(results: any) {
  const annotations = results.annotationResults[0]
  
  // Extract labels
  const labels = annotations.segmentLabelAnnotations?.map((label: any) => ({
    label: label.entity.description,
    confidence: label.segments[0].confidence
  })).slice(0, 10) || []
  
  // Count shot changes
  const shotCount = annotations.shotAnnotations?.length || 0
  
  // Extract transcript
  let transcript = ''
  if (annotations.speechTranscriptions) {
    for (const transcription of annotations.speechTranscriptions) {
      for (const alternative of transcription.alternatives) {
        transcript += alternative.transcript + ' '
      }
    }
  }
  
  // Calculate duration
  const duration = annotations.segment 
    ? parseFloat(annotations.segment.endTimeOffset.slice(0, -1))
    : 0
  
  return {
    labels,
    shotCount,
    transcript: transcript.trim(),
    duration,
    rawAnnotations: annotations
  }
}

// supabase/functions/send-analysis-notification/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.7.1'

serve(async (req) => {
  try {
    const { record } = await req.json()
    
    // Only send notification when analysis is completed
    if (record.status !== 'completed') {
      return new Response(JSON.stringify({ skip: true }), { status: 200 })
    }
    
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )
    
    // Get user email
    const { data: profile } = await supabaseClient
      .from('profiles')
      .select('email')
      .eq('id', record.user_id)
      .single()
    
    if (!profile) {
      throw new Error('User profile not found')
    }
    
    // Here you would integrate with your email service
    // For example, using SendGrid, Resend, etc.
    console.log(`Would send email to ${profile.email} about analysis ${record.id}`)
    
    return new Response(JSON.stringify({ success: true }), { status: 200 })
    
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }), 
      { status: 500 }
    )
  }
})

// supabase/functions/.env.example
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key
GOOGLE_API_KEY=your-google-api-key
BACKEND_URL=https://your-backend.railway.app
SERVICE_AUTH_KEY=shared-secret-for-internal-calls

// Deploy commands for Supabase Edge Functions
// Run these in your project root:

// 1. Login to Supabase CLI
// supabase login

// 2. Link to your project
// supabase link --project-ref your-project-ref

// 3. Deploy functions
// supabase functions deploy process-video
// supabase functions deploy send-analysis-notification

// 4. Set secrets
// supabase secrets set GOOGLE_API_KEY=your-key
// supabase secrets set BACKEND_URL=https://your-backend.railway.app
// supabase secrets set SERVICE_AUTH_KEY=your-secret