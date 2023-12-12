window.dragable = (element) => {
    var x1 = 0, y1 = 0, x2 = 0, y2 = 0;
    const logWindow = document.getElementById(element.id + "-header")
    logWindow.onmousedown = dragMouseDown;
  
    function dragMouseDown(e) {
      e = e || window.event;
      e.preventDefault();
      // get the mouse cursor position at startup:
      x2 = e.clientX;
      y2 = e.clientY;
      document.onmouseup = closeDragElement;
      // call a function whenever the cursor moves:
      document.onmousemove = elementDrag;
    }
  
    function elementDrag(e) {
      e = e || window.event;
      e.preventDefault();
      // calculate the new cursor position:
      x1 = x2 - e.clientX;
      y1 = y2 - e.clientY;
      x2 = e.clientX;
      y2 = e.clientY;
      // set the element's new position:
      element.style.top = (element.offsetTop - y1) + "px";
      element.style.left = (element.offsetLeft - x1) + "px";
    }
  
    function closeDragElement() {
      // stop moving when mouse button is released:
      document.onmouseup = null;
      document.onmousemove = null;
    }
  }