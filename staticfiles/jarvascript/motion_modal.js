const motionModal = document.getElementById('motion-modal');
const motionContent = document.getElementById('motion-content');
const infoSlideContent = document.getElementById('info-slide-content');
const motionButton = document.getElementsByClassName('motion-button');
const closeModal = document.getElementsByClassName('close-modal');

function showMotion(motion, infoSlide) {
    motionModal.style.display = 'block';
    motionContent.innerHTML = motion;
    infoSlideContent.innerHTML = infoSlide;
}

function closeMotion() {
    motionModal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == motionModal) {
        motionModal.style.display = 'none';
    }
}
