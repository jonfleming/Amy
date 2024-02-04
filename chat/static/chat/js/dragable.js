window.dragable = (container, header) => {
    var x1 = 0, y1 = 0, x2 = 0, y2 = 0;
    header.onpointerdown = dragMouseDown;
    header.ontouchstart = dragMouseDown;
  
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
      
      container.style.top = (container.offsetTop - y1) + "px";
      container.style.left = (container.offsetLeft - x1) + "px";
    }
  
    function closeDragElement() {
      document.onmouseup = null;
      document.onmousemove = null;
      document.onpointermove = null;
    }
  }
