document.addEventListener("DOMContentLoaded", function () {
    // Select all update-cart buttons
    const updateCartButtons = document.querySelectorAll(".update-cart");

    // Add click event listeners to each button
    updateCartButtons.forEach(button => {
        button.addEventListener("click", function () {
            const productId = this.dataset.product; // Product ID from data attribute
            const action = this.dataset.action; // Action (add, remove, clear_out)

            // Debugging
            console.log(`Action triggered: ${action}, Product ID: ${productId}`);

            // Send POST request to update the cart
            fetch("add_to_cart/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"), // Include CSRF token
                },
                body: JSON.stringify({
                    product_id: productId,
                    action: action,
                }),
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Update cart totals dynamically
                        document.querySelector("#cart-total-items").textContent = data.cart.total_items;
                        document.querySelector("#cart-total-amount").textContent = `$${data.cart.total_amount.toFixed(2)}`;

                        // Update item quantity and subtotal dynamically
                        const quantitySpan = document.querySelector(
                            `.update-cart[data-product="${productId}"][data-action="remove"]`
                        )?.nextElementSibling;
                        if (quantitySpan) {
                            quantitySpan.textContent = data.cart.items[productId]?.quantity || 0;
                        }

                        const subtotalElement = document.querySelector(
                            `.update-cart[data-product="${productId}"][data-action="add"]`
                        )?.closest(".grid")?.querySelector(".subtotal");
                        if (subtotalElement) {
                            subtotalElement.textContent = `$${(
                                (data.cart.items[productId]?.quantity || 0) *
                                data.cart.items[productId]?.price
                            ).toFixed(2)}`;
                        }

                        // Remove product from the DOM if quantity is zero
                        if (!data.cart.items[productId]) {
                            const productElement = document.querySelector(`[data-product="${productId}"]`);
                            if (productElement) {
                                productElement.closest(".grid").remove();
                            }
                        }
                    } else {
                        console.error("Error updating cart:", data.message);
                    }
                })
                .catch(error => {
                    console.error("Error updating cart:", error);
                });
        });
    });

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(`${name}=`)) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
