let confirmPopupVisible = false;
let confirmChoice = 'yes';
const eventSource = new EventSource("/stats_feed");

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById('fps').textContent = data.fps;
    document.getElementById('model').textContent = data.model;
    document.getElementById('numPoses').textContent = data.numPoses;
};

eventSource.onerror = function(error) {
    console.error("SSE connection error", error);
};

document.addEventListener('DOMContentLoaded',()=>{
  document.addEventListener('keydown',(event) =>{
    const key = event.key;
    const path = window.location.pathname;

    //welcome page 
    if (path === '/' && key === 'Enter'){
      window.location.href = '/options';
    }

    //Options page 

if (path === '/options') {
    const options = document.querySelectorAll('.filter-option');
    let selectedIndex = 0;

    const updateSelection = () => {
        options.forEach((el, idx) => {
            el.classList.toggle('selected', idx === selectedIndex);
        });
        options[selectedIndex].scrollIntoView({ behavior: 'smooth', inline: 'center' });
    };

    document.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowRight') {
            selectedIndex = (selectedIndex + 1) % options.length;
            updateSelection();
        } else if (event.key === 'ArrowLeft') {
            selectedIndex = (selectedIndex - 1 + options.length) % options.length;
            updateSelection();
        } else if (event.key === 'Enter') {
            const selectedFilter = options[selectedIndex].dataset.filter;
            window.location.href = `/photobooth?filter=${encodeURIComponent(selectedFilter)}`;
        }
    });

    updateSelection();  // initial highlight
}


  if (path == '/photobooth' && key == 'Enter'){
    window.location.href = '/qrcode';
  }
    
  if (path === '/qrcode') {
  const popup = document.getElementById('confirm-popup');
  const yesBtn = document.getElementById('confirm-yes');
  const noBtn = document.getElementById('confirm-no');

  // Trigger confirmation popup
  if (!confirmPopupVisible && key === 'Enter') {
      popup.style.display = 'block';
      confirmPopupVisible = true;
      confirmChoice = 'yes';
      yesBtn.classList.add('selected');
      noBtn.classList.remove('selected');
      return;
  }

  // Handle arrow selection
  if (confirmPopupVisible && (key === 'ArrowLeft' || key === 'ArrowRight')) {
      confirmChoice = confirmChoice === 'yes' ? 'no' : 'yes';
      yesBtn.classList.toggle('selected', confirmChoice === 'yes');
      noBtn.classList.toggle('selected', confirmChoice === 'no');
      return;
  }

  // Confirm selection
  if (confirmPopupVisible && key === 'Enter') {
      if (confirmChoice === 'yes') {
          window.location.href = '/';
      } else {
          popup.style.display = 'none';
          confirmPopupVisible = false;
      }
  }
  }

  })
})
