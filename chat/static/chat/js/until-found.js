document.querySelectorAll('.section').forEach((section) => {
  section.onbeforematch = () => {
    section.classList.remove('collapsed-response')
  }
  section.querySelector('.user-text').onclick = (e) => {
    const target = e.target
    target.contentEditable = true
  }
  section.querySelector('.user-text').addEventListener('keydown', (event) => {
    if (event.keyCode === 13) {
      event.preventDefault()
      const span = event.target
      const text = span.textContent      
      const text_id = span.id

      fetch("/reindex/?command=save", {
        method: "POST",
        body: JSON.stringify({ id: text_id, text }),
      }).catch((err) => console.log(err))
    }
  })
  section.querySelector('.show-prompt, .prompt').onclick = (e) => {
    e.stopPropagation()
    section.classList.toggle('collapsed-prompt')

    const prompt = section.querySelector('.prompt')
    if (section.classList.contains('collapsed-prompt')) {
      prompt.hidden = 'until-found'
    } else {
      prompt.removeAttribute('hidden')
    }
  }
  section.querySelector('.show-response, .response').onclick = () => {
    section.classList.toggle('collapsed-response')

    const response = section.querySelector('.response')
    if (section.classList.contains('collapsed-response')) {
      response.hidden = 'until-found'
    } else {
      response.removeAttribute('hidden')
    }
  }  
})
