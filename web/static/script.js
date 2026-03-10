document.addEventListener('DOMContentLoaded', () => {
    const orderTypeSelect = document.getElementById('order_type');
    const priceInput = document.getElementById('price');
    const sideSelect = document.getElementById('side');

    // Toggle price input based on order type
    orderTypeSelect.addEventListener('change', (e) => {
        if (e.target.value === 'LIMIT') {
            priceInput.disabled = false;
            priceInput.placeholder = 'Enter limit price';
            priceInput.required = true;
        } else {
            priceInput.disabled = true;
            priceInput.placeholder = 'Market';
            priceInput.value = '';
            priceInput.required = false;
        }
    });

    // Update side color
    const updateSideColor = () => {
        if (sideSelect.value === 'BUY') {
            sideSelect.style.color = 'var(--success)';
        } else {
            sideSelect.style.color = 'var(--danger)';
        }
    };
    sideSelect.addEventListener('change', updateSideColor);
    updateSideColor(); // initial call

    // Place Order handler
    document.getElementById('orderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('placeOrderBtn');
        const statusEl = document.getElementById('orderStatus');
        
        btn.textContent = 'Processing...';
        btn.disabled = true;
        statusEl.className = 'status-msg';
        statusEl.textContent = '';

        const payload = {
            symbol: document.getElementById('symbol').value,
            side: document.getElementById('side').value,
            order_type: document.getElementById('order_type').value,
            quantity: parseFloat(document.getElementById('quantity').value)
        };
        
        if (payload.order_type === 'LIMIT') {
            payload.price = parseFloat(priceInput.value);
        }

        try {
            const res = await fetch('/api/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (res.ok) {
                statusEl.textContent = `Order placed! ID: ${data.orderId}`;
                statusEl.className = 'status-msg success';
                
                // Auto-fill the verifier
                document.getElementById('verify_symbol').value = payload.symbol;
                document.getElementById('verify_order_id').value = data.orderId;
            } else {
                statusEl.textContent = `Error: ${data.detail || 'Failed'}`;
                statusEl.className = 'status-msg error';
            }
        } catch (err) {
            statusEl.textContent = `Error: ${err.message}`;
            statusEl.className = 'status-msg error';
        } finally {
            btn.textContent = 'Submit Order';
            btn.disabled = false;
        }
    });

    // Verify Order handler
    document.getElementById('verifyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('verifyBtn');
        const statusEl = document.getElementById('verifyStatus');
        const resultBox = document.getElementById('orderResultBox');
        const resultContent = document.getElementById('orderResultContent');
        
        btn.textContent = 'Checking...';
        btn.disabled = true;
        statusEl.className = 'status-msg';
        statusEl.textContent = '';
        resultBox.classList.add('hidden');

        const symbol = document.getElementById('verify_symbol').value;
        const orderId = document.getElementById('verify_order_id').value;

        try {
            const res = await fetch(`/api/order/${symbol}/${orderId}`);
            const data = await res.json();
            
            if (res.ok) {
                resultContent.textContent = JSON.stringify(data, null, 2);
                resultBox.classList.remove('hidden');
                statusEl.className = 'status-msg'; // hide
            } else {
                statusEl.textContent = `Error: ${data.detail || 'Not Found'}`;
                statusEl.className = 'status-msg error';
            }
        } catch (err) {
            statusEl.textContent = `Error: ${err.message}`;
            statusEl.className = 'status-msg error';
        } finally {
            btn.textContent = 'Check Status';
            btn.disabled = false;
        }
    });
});
