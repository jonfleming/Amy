window.connect()

let speechRecognition = new webkitSpeechRecognition()
let voicInterval = setInterval(getZiraVoice, 1000)
let stopListening = false
let zira, cutOffInterval, StartListeningTimeout, sleeping = false, listening = false
let delay_before_cutoff = 1500
let wake_word_delay = 2000
let stats_delay = 2000
let useAvatar = true
let nolog = false // ignore "no-speech" restarts

if ('webkitSpeechRecognition' in window) {
  const user_text = document.getElementById('user_text')
  const status = document.getElementById('status')
  const submit = document.getElementById('submit')
  const start = document.getElementById('start')
  const command = document.getElementById('command')

  const micOn = (text) => {
    window.log(`micOn(${text})`)
    start.innerHTML = `<i class="fa fa-microphone"></i>&nbsp;&nbsp;${text}`
    start.classList.add("btn-danger")
    start.classList.remove("btn-primary")
    status.innerHTML = 'Listening...'
  }

  const micOff = (text) => {
    window.log(`micOff(${text})`)
    start.innerHTML = `<i class="fa fa-microphone"></i>&nbsp;&nbsp;${text}`
    start.classList.add("btn-primary")
    start.classList.remove("btn-danger")
  }

  let final_transcript = ''
  let listening = false

  speechRecognition.continuous = true
  speechRecognition.interimResults = true
  speechRecognition.lang = ''

  speechRecognition.onstart = () => {
    window.log(`🟢 sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)
    listening = true
    stopListening = false
    user_text.value = ''
    if (!sleeping) {
      micOn("Stop")
      // status.innerHTML = "Listening ..."
    }
  }

  speechRecognition.onend = () => {
    listening = false
    status.innerHTML = ''
    final_transcript = ''
    window.log(`🔴 sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)

    micOff('Start')

    if (user_text.value) {
      status.innerHTML = 'Thinking ...'
      submit.click()
    } 
    
    status.innerHTML = 'Stopped Listening.'
      
    if (!stopListening) {
      window.log('🞙 Restart Listening')
      startListening()
      window.nolog = true
    }
  }

  speechRecognition.onresult = (event) => {
    clearInterval(cutOffInterval)
    let interim_transcript = ''

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final_transcript += ' ' + event.results[i][0].transcript
      } else {
        interim_transcript += event.results[i][0].transcript
      }
    }

    status.innerHTML = interim_transcript

    if (sleeping) {
      if (interim_transcript.toLowerCase().includes("amy")) {
        micOn("Awake")
        sleeping = false
      } else {
        final_transcript = ''
      }
    }

    if (final_transcript && !sleeping) {
      window.log('🔈 Transcribed: ' + final_transcript)
      cutOffInterval = setInterval(proceed, delay_before_cutoff)
      user_text.value = final_transcript      
    }
    
  }

  speechRecognition.onerror = (event) => {
    window.log(`🞋 Error event: ${JSON.stringify(event, null, 2)} error: ${event.error}`)
    window.log(`🞋 sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)
    status.innerHTML = ''
    if (event.isTrusted) {
      window.log('🞙 ignoring isTrusted event')
    } else if (event.error !== 'no-speech') {
      stopListening = true
      sleeping = false
    }
  }
  
  start.onclick = (event) => {
    let btnText = 'Start'
    if (start.innerHTML.includes('Stop')) {
      btnText = 'Stop'
    }
    window.log(`=== === ${btnText} Click === === `)
    event.preventDefault()

    if (sleeping || !listening) {
      window.log(`>>> [Wakeup] sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)
      window.log(`>>> command: ${command.value}`)
      if (["START", "INTRO"].includes(command.value)) {
        enableSpeech()
        myHandler()
      } else {
        sleeping = false
        if (!listening) {
          startListening()
        } else {
          micOn("Stop")
        }
      }
    } else {
      stopListening = true
      speechRecognition.stop() // triggers onend

      sleeping = true
      window.log(`🞙 Sleeping.  Wait for wake word (timeout ${wake_word_delay})`)
      window.log(`<<< sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)
      StartListeningTimeout = setTimeout(startListening, wake_word_delay)
      window.stopStats()
    }
  }
} else {
  window.log('🞋 Speech Recognition Not Available')
}

function proceed() {
  window.nolog = false
  window.log('🞙 Process user text')
  clearInterval(cutOffInterval)
  stopListening = true
  speechRecognition.stop()
}

function streamingCallback(done) {
  window.log(`🞙 Streaming Callback - ${done ? 'Done' : 'Still going'}`)
  window.log(`    sleeping: ${sleeping}, listening ${listening}, stopListening ${stopListening}`)
  if (done) {
    // Done playing video
    if (!listening) {
      startListening()
    }
  } else {    
    // Still playing video
    if (listening) {
      stopListening = true
      speechRecognition.stop()  
    }
  }
}

async function speak(text) {
  window.log('🞙 Amy Speaking')
  stopListening = true
  speechRecognition.stop()

  if (useAvatar) {
    try {
      window.startStats(streamingCallback, stats_delay)
      await window.talk(text, speakNoVideo)
    } catch (e) {
      window.log("🞙 Error retrieving video: " + e)
      useAvatar = false
      speakNoVideo(text)
    }
    
  } else {
    speakNoVideo(text)
  }
}

function speakNoVideo(text) {
  const output = new SpeechSynthesisUtterance(text)
  output.voice = zira
  output.volume = window.volume
  output.onend = (event) => {
    startListening()
  }
  window.speechSynthesis.speak(output)
}

function startListening() {
  if (listening) {    
    window.log('🞙 Already listening')
    stopListening = false
    return
  }

  window.log('🞙 Resume Listening')

  try {
    speechRecognition.start()
  } catch (err) {
    if (!err.message.includes('already started')) {
      window.log(`startListening Error: ${JSON.stringify(err, null, 2)}`)
      window.log(`Already started `, err)
    }
  }
}

function clearIntervals() {
  window.log('🞙 Clear all intervals')

  clearTimeout(StartListeningTimeout)
  clearInterval(cutOffInterval)
  clearInterval(voicInterval)
  
  stopListening = true
  sleeping = false
  window.stopStats()
  speechRecognition.stop() // triggers onend
}

function getZiraVoice() {
  const voice = speechSynthesis.getVoices()

  if (voice.length > 0) {
    clearInterval(voicInterval)
    zira = speechSynthesis.getVoices().filter(function (voice) {
      return voice.name.includes('Zira')
    })[0]
  }
}

function thought(text) {
  const conversation = document.getElementById("conversation")

  conversation.innerHTML += `<p class="row w-75 float-end p-2 bubble-right mb-1 text-black rounded-pill" 
      style="background-color: #f8f8f8">${text}</p>`
  main.scrollTo(0, main.scrollHeight)
}

