document.querySelectorAll(".section").forEach((section) => {
  section.onbeforematch = () => {
    section.classList.remove("collapsed-response")
  }
  section.querySelector(".user-text").onclick = () => {
    section.classList.toggle("collapsed-response")

    const response = section.querySelector(".response")
    if (section.classList.contains("collapsed-response")) {
      response.hidden = "until-found"
    } else {
      response.removeAttribute("hidden")
    }
  }
  section.querySelector(".response").onclick = () => {
    section.classList.toggle("collapsed-response")

    const response = section.querySelector(".response")
    if (section.classList.contains("collapsed-response")) {
      response.hidden = "until-found"
    } else {
      response.removeAttribute("hidden")
    }
  }  
  section.querySelector(".show-prompt").onclick = (e) => {
    e.stopPropagation()
    section.classList.toggle("collapsed-prompt")

    const prompt = section.querySelector(".prompt")
    if (section.classList.contains("collapsed-prompt")) {
      prompt.hidden = "until-found"
    } else {
      prompt.removeAttribute("hidden")
    }
  }
  section.querySelector(".prompt").onclick = (e) => {
    e.stopPropagation()
    section.classList.toggle("collapsed-prompt")

    const prompt = section.querySelector(".prompt")
    if (section.classList.contains("collapsed-prompt")) {
      prompt.hidden = "until-found"
    } else {
      prompt.removeAttribute("hidden")
    }
  }
})
