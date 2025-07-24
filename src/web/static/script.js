let confirmPopupVisible = false;
let confirmChoice = 'yes';



function scrollElementIntoCenter(container, element) {
  const containerRect = container.getBoundingClientRect();
  const elementRect = element.getBoundingClientRect();
  const scrollLeft = container.scrollLeft;
  const elementCenter = element.offsetLeft + element.offsetWidth / 2;
  const containerCenter = container.clientWidth / 2;
  container.scrollTo({
    left: elementCenter - containerCenter,
    behavior: 'smooth'
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;

  // Welcome page
  if (path === '/') {
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        window.location.href = '/options';
      }
    });
  }

  // Options page
  if (path === '/options') {
    const options = document.querySelectorAll('.filter-option');
    let selectedIndex = 0;

  const updateSelection = () => {
    options.forEach((el, idx) => {
      el.classList.toggle('selected', idx === selectedIndex);
    });
    scrollElementIntoCenter(options[selectedIndex].parentElement, options[selectedIndex]);
  };

    updateSelection();  // Initial highlight

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
  }

  // Photobooth page
  if (path === '/photobooth') {
    /*
    const eventSource = new EventSource("/stats_feed");

    eventSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      document.getElementById('fps').textContent = data.fps;
      document.getElementById('model').textContent = data.model;
      document.getElementById('numPoses').textContent = data.numPoses;
    };

    eventSource.onerror = function(error) {
      console.error("SSE connection error", error);
      // Optional: stop retry attempts
      eventSource.close();
    }; */
    
    document.addEventListener('keydown', (event) => {
      console.log('key pressed in photobooth')
      if (event.key === 'Enter') {
        fetch('/capture_photo', {
          method: 'POST'
        }) ;
        window.location.href = '/qrcode';
      }
    });
  }

  // QR Code confirmation page
  if (path === '/qrcode') {
    const popup = document.getElementById('confirm-popup');
    const yesBtn = document.getElementById('confirm-yes');
    const noBtn = document.getElementById('confirm-no');
    let confirmPopupVisible = false;
    let confirmChoice = 'yes';

    document.addEventListener('keydown', (event) => {
      const key = event.key;

      if (!confirmPopupVisible && key === 'Enter') {
        popup.style.display = 'block';
        confirmPopupVisible = true;
        confirmChoice = 'yes';
        yesBtn.classList.add('selected');
        noBtn.classList.remove('selected');
        return;
      }

      if (confirmPopupVisible && (key === 'ArrowLeft' || key === 'ArrowRight')) {
        confirmChoice = confirmChoice === 'yes' ? 'no' : 'yes';
        yesBtn.classList.toggle('selected', confirmChoice === 'yes');
        noBtn.classList.toggle('selected', confirmChoice === 'no');
        return;
      }

      if (confirmPopupVisible && key === 'Enter') {
        if (confirmChoice === 'yes') {
          window.location.href = '/';
        } else {
          popup.style.display = 'none';
          confirmPopupVisible = false;
        }
      }
    });
  }
});
