const DEBUG = false
const main = document.querySelector('.main')
const mainForm = document.getElementById('main-form')
const conversation = document.getElementById('conversation')
const user = document.getElementById('user')
const userLabel = document.getElementById('user-label')
const command = document.getElementById('command')
const utterance = document.getElementById('utterance')
const status = document.getElementById('status')
const submit = document.getElementById('submit')
const start = document.getElementById('start')

document.addEventListener(
  'DOMContentLoaded',
  function () {
    mainForm.addEventListener('submit', (event) => {
      event.preventDefault()
      myHandler()
    })
  },
  false
)

async function myHandler() {
  if (DEBUG) {
    appendFakeResponse()
  } else {
    appendUtterance()
    postForm()
      .then((response) => response.json())
      .then((data) => {
        user.innerHTML = data.user
        userLabel.innerHTML = data.user
        command.value = data.command
        const text = parse(data.text)
        appendResponse(text)
        speak(text)
        if (command.value == 'START') {
          command.value = 'INTRO'
        }
      })
  }

  return false
}

async function postForm() {
  const url = document.location.href
  const data = Object.fromEntries(new FormData(mainForm))

  const init = {
    method: 'POST',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/plain, */*',
      'X-CSRFToken': data.csrfmiddlewaretoken,
    },
    body: JSON.stringify(data),
  }

  utterance.value = ''
  const response = await fetch(url, init)

  return response
}

function parse(text) {
  return text.replace('<<USER>>', user.textContent)
}

function appendUtterance() {
  if (utterance.value) {
    conversation.innerHTML += `<p class="row w-75 float-end p-2 bubble mb-1 text-white rounded-3 bg-primary" 
      style="background-color: #f5f6f7">${utterance.value}</p>`
  }
}

function appendResponse(text) {
  if (text) {
    conversation.innerHTML += `<p class="row w-75 p-2 ml-5 mb-1 text-white rounded-3" 
      style="background-color: #8f8f8f">${text}</p>`
  }
  main.scrollTo(0, main.scrollHeight)
}

function appendFakeResponse() {
  appendUtterance()
  conversation.innerHTML += `<p class="row w-75 p-2 ml-5 mb-1 text-white rounded-3" 
    style="background-color: #8f8f8f">${scramble(utterance.value)}</p>`
  utterance.value = ''
  main.scrollTo(0, main.scrollHeight)
}

function scramble(a) {
  return a
    .split(' ')
    .sort(() => Math.random() - 0.5)
    .join(' ')
}
