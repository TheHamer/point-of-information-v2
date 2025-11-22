const deletUserModal = document.getElementById('delete-user-modal');
const deletUserButton = document.getElementsByClassName('delete-user-button');
const closeModal = document.getElementsByClassName('close-modal');

function showDeleteUserModal() {
    deletUserModal.style.display = 'block';
}

function closeDeleteUserModal() {
    deletUserModal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == deletUserModal) {
        deletUserModal.style.display = 'none';
    }
}
