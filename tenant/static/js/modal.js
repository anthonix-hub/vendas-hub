// modal.js

document.addEventListener('DOMContentLoaded', () => {
    const itemButtons = document.querySelectorAll('.view-item-details');
    const modal = document.getElementById('itemDetailsModal');
    const modalContent = document.getElementById('itemDetailsContent');
    const closeModalButton = document.getElementById('closeModal');

    itemButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.product;
            fetchItemDetails(productId);
        });
    });

    closeModalButton.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    function fetchItemDetails(productId) {
        fetch(`/item_details/${productId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            }
        })
        .then(response => response.json())
        .then(data => {
            displayItemDetails(data);
            modal.classList.remove('hidden');
        });
    }

    function displayItemDetails(data) {
        modalContent.innerHTML = `
            <h2 class="text-xl font-bold mb-4">${data.name}</h2>
            <img src="${data.imageURL}" alt="${data.name}" class="mb-4">
            <p class="mb-2"><strong>Price:</strong> #${data.price}</p>
            <p class="mb-2"><strong>Description:</strong> ${data.description}</p>
            <!-- Add more attributes as needed -->
        `;
    }
});
