const amy_modal = document.getElementById("amy_modal")

function showModal() {
  fetch("/profile", {
    method: "GET",
  })
    .then((response) => {
      response.text().then((data) => {
        amy_modal.innerHTML = data
      })
    })
    .catch((err) => console.log(err))

  amy_modal.style.display = "block"
}

function closeModal(event) {
  event.preventDefault()
  postForm('/profile/')
    .then((response) => {
      response.text().then((body) => {
        if (body) {
          amy_modal.innerHTML = body
        } else {
          amy_modal.style.display = "none"
        }
      })
    })
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
  if (event.target == amy_modal) {
    closeModal(event)
  }
}

async function postForm(url) {
  const form = document.getElementById("profile_form")
  const data = Object.fromEntries(new FormData(form))

  const init = {
    method: "POST",
    mode: "cors",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/plain, */*",
      "X-CSRFToken": data.csrfmiddlewaretoken,
    },
    body: JSON.stringify(data),
  }

  const response = await fetch(url, init)

  return response
}
