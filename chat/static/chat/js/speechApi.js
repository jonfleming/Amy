let speechRecognition = new webkitSpeechRecognition()
let voicInterval = setInterval(getZiraVoice, 1000)
let stopListening = false
let zira, output, cutOffInterval

if ('webkitSpeechRecognition' in window) {
  const utterance = document.getElementById('utterance')
  const status = document.getElementById('status')
  const submit = document.getElementById('submit')
  const start = document.getElementById('start')
  const command = document.getElementById('command')

  let final_transcript = ''
  let listening = false

  speechRecognition.continuous = true
  speechRecognition.interimResults = true
  speechRecognition.lang = ''

  speechRecognition.onstart = () => {
    console.log('Speech Recognition Starting')
    listening = true
    stopListening = false
    utterance.value = ''
    micOn('Stop')
  }

  const micOn = (text) => {
    start.innerHTML = `<i class="fa fa-microphone"></i>&nbsp;&nbsp;${text}`
    start.classList.add('btn-danger')
    start.classList.remove('btn-primary')
    status.innerHTML = "Listening ...";
  }

  const micOff = (text) => {
    start.innerHTML = `<i class="fa fa-microphone"></i>&nbsp;&nbsp;${text}`
    start.classList.add('btn-primary')
    start.classList.remove('btn-danger')
  }

  speechRecognition.onerror = (event) => {
    console.log('Speech Recognition Error', event)
    status.innerHTML = ''
    if (event.error !== 'no-speech') {
      stopListening = true
    }
  }

  speechRecognition.onend = () => {
    console.log('Speech Recognition Ended')
    listening = false
    status.innerHTML = ''
    final_transcript = ''

    micOff('Stop')

    if (utterance.value) {
      status.innerHTML = 'Thinking ...'
      submit.click()
    } else if (!stopListening) {
      startListening();
    } else {
      status.innerHTML = 'Stopped Listening.'
    }

  }

  speechRecognition.onresult = (event) => {
    clearInterval(cutOffInterval)
    let interim_transcript = ''

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final_transcript += event.results[i][0].transcript
      } else {
        interim_transcript += event.results[i][0].transcript
      }
    }

    if (final_transcript) {
      cutOffInterval = setInterval(proceed, 2000)
      utterance.value = final_transcript
    }

    if (
      interim_transcript.toLowerCase().includes("amy") ||
      final_transcript.toLowerCase().includes("amy")
    ) {
      micOn('Awake')
    }
    document.querySelector('#status').innerHTML = interim_transcript
  }

  start.onclick = (event) => {
    event.preventDefault()

    if (!listening) {
      if (command.value === 'START') {
        myHandler()
      } else {
        startListening()
      }
    } else {
      speechRecognition.stop()
    }
  }
} else {
  console.log('Speech Recognition Not Available')
}

function proceed() {
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
  stopListening = true
  speechRecognition.stop()

  output = new SpeechSynthesisUtterance(text)
  output.voice = zira
  output.onend = (event) => {
    startListening()
  }

  window.speechSynthesis.speak(output)
}

function startListening() {
  try {
    speechRecognition.start();
  } catch (err) {
    console.log(`Already started `, err)
  }

  status.innerHTML = "Listening ...";
}
