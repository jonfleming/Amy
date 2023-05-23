let speechRecognition = new webkitSpeechRecognition()
let voicInterval = setInterval(getZiraVoice, 1000)
let stopListening = false
let zira, output, cutOffInterval, sleeping = false
let delay_fefore_cutoff = 3000

if ('webkitSpeechRecognition' in window) {
  const user_text = document.getElementById('user_text')
  const status = document.getElementById('status')
  const submit = document.getElementById('submit')
  const start = document.getElementById('start')
  const command = document.getElementById('command')

  const micOn = (text) => {
    info('micOn')
    start.innerHTML = `<i class="fa fa-microphone"></i>&nbsp;&nbsp;${text}`
    start.classList.add("btn-danger")
    start.classList.remove("btn-primary")
    status.innerHTML = 'Listening...'
  }

  const micOff = (text) => {
    info('micOff')
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
    info('onstart')
    info(`--- sleeping: ${sleeping}, listening ${listening}`)
    console.log('Speech Recognition Starting')
    listening = true
    stopListening = false
    user_text.value = ''
    if (!sleeping) {
      micOn("Stop")
      // status.innerHTML = "Listening ..."
    }
  }

  speechRecognition.onend = () => {
    info('onend')
    info(`=== sleeping: ${sleeping}, listening ${listening}`)
    console.log('Speech Recognition Ended')
    listening = false
    status.innerHTML = ''
    final_transcript = ''

    micOff('Start')

    if (user_text.value) {
      status.innerHTML = 'Thinking ...'
      submit.click()
    } 
    
    status.innerHTML = 'Stopped Listening.'
      
    if (!stopListening) {
      startListening()
    }
  }

  speechRecognition.onresult = (event) => {
    info('onresult')
    clearInterval(cutOffInterval)
    let interim_transcript = ''

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final_transcript += event.results[i][0].transcript
      } else {
        interim_transcript += event.results[i][0].transcript
      }
    }

    console.log(final_transcript)

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
      cutOffInterval = setInterval(proceed, delay_fefore_cutoff)
      user_text.value = final_transcript
    }
    
  }

  speechRecognition.onerror = (event) => {
    info(`onerror event: ${JSON.stringify(event, null, 2)} error: ${event.error}`)
    info(`+++ sleeping: ${sleeping}, listening ${listening}`)
    console.log('Speech Recognition Error', event)
    status.innerHTML = ''
    if (event.isTrusted) {
      info('ignoring isTrusted event')
    } else if (event.error !== 'no-speech') {
      stopListening = true
      sleeping = false
    }
  }
  
  start.onclick = (event) => {
    info("=== === start.onclick === === ")
    event.preventDefault()
    info(`preventDefault`)

    if (sleeping || !listening) {
      info(`>>> sleeping: ${sleeping}, listening ${listening}`)
      info(`>>> command: ${command.value}`)
      if (command.value === 'START') {
        myHandler()
      } else {
        sleeping = false
        if (!listening) {
          startListening()
        } else {
          micOn('Stop')
        }
      }
    } else {
      stopListening = true
      speechRecognition.stop() // triggers onend

      sleeping = true
      info(`>>> timeout 2000`)
      info(`<<< sleeping: ${sleeping}, listening ${listening}`)
      setTimeout(startListening, 2000)
    }
  }
} else {
  console.log('Speech Recognition Not Available')
}

function proceed() {
  info('proceed')
  clearInterval(cutOffInterval)
  speechRecognition.stop()
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

function speak(text) {
  info('speak')
  stopListening = true
  speechRecognition.stop()

  output = new SpeechSynthesisUtterance(text)
  output.voice = zira
  output.volume = window.volume
  output.onend = (event) => {
    startListening()
  }

  window.speechSynthesis.speak(output)
}

function startListening() {
  info('startListening')
  try {
    speechRecognition.start()
  } catch (err) {
    info(`startListening Error: ${JSON.stringify(err, null, 2)}`)
    console.log(`Already started `, err)
  }
}

function info(text) {
  const user = document.getElementById('user')
  const conversation = document.getElementById("conversation")
  const msg = sessionStorage.getItem('msgbox') + '\n' + text
  sessionStorage.setItem('msgbox', msg)

  if (user.value === 'DEBUG') {
    conversation.innerHTML += `<p class="row w-75 float-end p-2 bubble-right mb-1 text-black rounded-pill" 
        style="background-color: #f8f8f8">${text}</p>`
    main.scrollTo(0, main.scrollHeight)
  }
}
