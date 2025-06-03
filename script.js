const counters = document.querySelectorAll('.counter');
const speed = 400; // Lower the number, faster the counter

counters.forEach(counter => {
    const updateCount = () => {
        const target = +counter.getAttribute('data-target');
        const count = +counter.innerText;

        const increment = target / speed;

        if (count < target) {
            counter.innerText = Math.ceil(count + increment);
            setTimeout(updateCount, 20); // Repeat the function every 20ms
        } else {
            counter.innerText = target;
        }
    };
    let options = {
        threshold: 0.10 // Trigger when the section is at least 50% visible
    };

    updateCount();
});


const images = [
    'BLANKET/ALLIANCE BOX 1.webp',
    'BLANKET/2.webp',
    'BLANKET/3.webp',
    'BLANKET/4.webp',
    'BLANKET/5.webp',
    'BLANKET/6.webp',
    'BLANKET/7.webp',
    'BLANKET/8.webp',
    'BLANKET/9.webp',
    'BLANKET/10.webp',
    'BLANKET/11.webp',
    'BLANKET/12.webp',
    
    // Add more image paths as needed
  ];
  
  let currentIndex = 0;
  
  function openModal() {
    document.getElementById('galleryModal').style.display = 'flex';
    document.getElementById('modalImage').src = images[currentIndex];
  }
  
  function closeModal() {
    document.getElementById('galleryModal').style.display = 'none';
  }
  
  function changeImage(direction) {
    currentIndex += direction;
  
    // Wrap around the array if we reach the end
    if (currentIndex < 0) {
      currentIndex = images.length - 1;
    } else if (currentIndex >= images.length) {
      currentIndex = 0;
    }
  
    document.getElementById('modalImage').src = images[currentIndex];
  }
// Selecting the hamburger button and menu
const hamburger = document.getElementById('hamburger');
const menu = document.getElementById('menu');

// Toggling the menu and hamburger active state
hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    menu.classList.toggle('open');
});

// Closing the menu when a link is clicked
menu.addEventListener('click', (event) => {
    if (event.target.tagName === 'A') {
        hamburger.classList.remove('active');
        menu.classList.remove('open');
    }
});
