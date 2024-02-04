const main = document.querySelector('.main')
const mainForm = document.getElementById('main_form')
const conversation = document.getElementById('conversation')
const user = document.getElementById('user')
const command = document.getElementById('command')
const user_text = document.getElementById('user_text')
const status = document.getElementById('status')
const submit = document.getElementById('submit')
const start = document.getElementById('start')
const display_name = document.getElementById('display_name')
const continue_text = document.getElementById("continue_text")
const log = document.getElementById("log")
const logHeader = document.getElementById("log-header")
const dragable = document.getElementById('dragable')

window.log = (msg) => {
  t = currentTime()
  log.value += t + ' ' + msg + '\n'
  log.scrollTop = log.scrollHeight;
}

function toggleLog() {
  dragable.style.display = dragable.style.display === 'none' ? 'block': 'none'
}

window.dragable(dragable, logHeader)

log.addEventListener('pointermove',()=>{
  logHeader.style.width = `${log.offsetWidth}px`;
})

function myHandler() {
  appendUserText()
  postForm(document.location.href)
    .then((response) => response.json())
    .then((data) => {
      // data = {user, text, command}
      if (user.value !== data.user) {
        user.value = data.user
        display_name.text = `Welcome, ${data.user}`
      }
      command.value = data.command
      const text = parse(data.text)
      appendResponse(text)
      speak(text)
      if (command.value == "START") {
        command.value = "INTRO"
      }
    })
    .catch((err) => window.log("🞋 Error posting user text: " + err))

  return false
}

async function postForm(url) {
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

  user_text.value = ''
  const response = await fetch(url, init)

  return response
}

function parse(text) {
  return text.replace('<<USER>>', user.textContent)
}

function appendUserText() {
  if (user_text.value) {
    conversation.innerHTML += `<p class="row w-85 float-end p-2 bubble-right mb-1 text-white rad bg-primary" 
      style="background-color: #f5f6f7">${user_text.value}</p>`
  }
}

function appendResponse(text) {
  if (text) {
    conversation.innerHTML += `<p class="row w-75 p-2 mb-1 text-white rad" 
      style="background-color: #8f8f8f">${text}</p>`
  }
  main.scrollTo(0, main.scrollHeight)
}

function currentTime() {
  const now = new Date();

  const month = String(now.getMonth() + 1).padStart(2, '0'); // months start from 0
  const day = String(now.getDate()).padStart(2, '0');
  const year = now.getFullYear().toString().substr(-2); // get last 2 digits of year

  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');

  return `${month}/${day}/${year} ${hours}:${minutes}:${seconds} `;
}
