const main = document.querySelector('.main')
const mainForm = document.getElementById('main-form')
const conversation = document.getElementById('conversation')
const user = document.getElementById('user')
const command = document.getElementById('command')
const utterance = document.getElementById('utterance')
const status = document.getElementById('status')
const submit = document.getElementById('submit')
const start = document.getElementById('start')
const display_name = document.getElementById('display_name')

if (command.value === "START" || command.value === "INTRO") {
  speechSynthesis.getVoices();
  setTimeout(myHandler, 2000);
}

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
  appendUtterance()
  postForm()
    .then((response) => response.json())
    .then((data) => {
      // data = {user, text, command}
      if (user.value !== data.user) {
        user.value = data.user;
        display_name.text = `Welcome, ${data.user}`;
      }
      command.value = data.command
      const text = parse(data.text)
      appendResponse(text)
      speak(text)
      if (command.value == 'START') {
        command.value = 'INTRO'
      }
    })

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
    conversation.innerHTML += `<p class="row w-75 float-end p-2 bubble-right mb-1 text-white rounded-pill bg-primary" 
      style="background-color: #f5f6f7">${utterance.value}</p>`
  }
}

function appendResponse(text) {
  if (text) {
    conversation.innerHTML += `<p class="row w-75 p-2 mb-1 text-white rounded-pill" 
      style="background-color: #8f8f8f">${text}</p>`
  }
  main.scrollTo(0, main.scrollHeight)
}
