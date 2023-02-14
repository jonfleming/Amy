let speechRecognition = new webkitSpeechRecognition()
let interval

if ('webkitSpeechRecognition' in window) {
  const utterance = document.getElementById('utterance')
  const status = document.getElementById('status')
  const submit = document.getElementById('submit')
  const start = document.getElementById('start')

  let final_transcript = ''
  let stop = false
  let listening = false

  speechRecognition.continuous = true
  speechRecognition.interimResults = true
  speechRecognition.lang = ''

  speechRecognition.onstart = () => {
    console.log('Speech Recognition Starting')
    listening = true
    stop = false
    utterance.value = ''
    status.innerHTML = 'Listening ...'
    status.style.display = 'block'
  }

  speechRecognition.onerror = (event) => {
    console.log('Speech Recognition Error', event)
    status.style.display = 'none'
    if (event.error !== 'no-speech') {
      stop = true
    }
  }

  speechRecognition.onend = () => {
    console.log('Speech Recognition Ended')
    listening = false
    status.style.display = 'block'
    status.innerHTML = ''
    final_transcript = ''

    if (utterance.value) {
      status.style.display = 'block'
      status.innerHTML = 'Thinking ...'
      submit.click()
    }

    if (!stop) {
      speechRecognition.start()
    }
  }

  speechRecognition.onresult = (event) => {
    clearInterval(interval)
    let interim_transcript = ''

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        final_transcript += event.results[i][0].transcript
        interval = setInterval(proceed, 1000)
      } else {
        interim_transcript += event.results[i][0].transcript
      }
    }
    utterance.value = utterance.value + ' ' + final_transcript
    document.querySelector('#status').innerHTML = interim_transcript
  }

  start.onclick = () => {
    if (listening) {
      stop = true
      speechRecognition.stop()
    } else {
      speechRecognition.start()
    }
  }
} else {
  console.log('Speech Recognition Not Available')
}

function proceed() {
  clearInterval(interval)
  speechRecognition.stop()
}

