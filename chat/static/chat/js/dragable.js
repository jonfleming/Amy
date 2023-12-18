window.dragable = (element) => {
    var x1 = 0, y1 = 0, x2 = 0, y2 = 0;
    const logWindow = document.getElementById(element.id + "-header")
    logWindow.onpointerdown = dragMouseDown;
    logWindow.ontouchstart = dragMouseDown;
  
    function dragMouseDown(e) {
      e.preventDefault();

      x2 = e.clientX;
      y2 = e.clientY;

      document.onpointerup = closeDragElement;
      document.onmouseup = closeDragElement;
      document.onpointermove = elementDrag;
    }
  
    function elementDrag(e) {
      e.preventDefault();

      x1 = x2 - e.clientX;
      y1 = y2 - e.clientY;
      
      x2 = e.clientX;
      y2 = e.clientY;
      
      element.style.top = (element.offsetTop - y1) + "px";
      element.style.left = (element.offsetLeft - x1) + "px";
    }
  
    function closeDragElement() {
      document.onmouseup = null;
      document.onmousemove = null;
    }
  }
