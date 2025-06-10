// Add share input field
function addShare() {
    const container = document.getElementById('sharesContainer');
    const shareItem = document.createElement('div');
    shareItem.className = 'share-item';
    shareItem.innerHTML = `
        <div class="share-item">
            <input type="text" class="form-control" placeholder="Person" required>
            <select class="form-control" required>
                <option value="percentage">Percentage</option>
                <option value="exact">Exact Amount</option>
            </select>
            <input type="number" class="form-control" placeholder="Value" required>
            <button type="button" class="btn btn-danger btn-sm" onclick="removeShare(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    container.appendChild(shareItem);
}

// Remove share input field
function removeShare(button) {
    button.closest('.share-item').remove();
}

// Fetch and display analytics
async function fetchAnalytics() {
    try {
        const [categoryRes, monthlyRes, expensiveRes] = await Promise.all([
            fetch('/api/v1/analytics/category-summary'),
            fetch('/api/v1/analytics/monthly-summary'),
            fetch('/api/v1/analytics/most-expensive')
        ]);

        const categoryData = await categoryRes.json();
        const monthlyData = await monthlyRes.json();
        const expensiveData = await expensiveRes.json();

        // Display category summary
        const categorySummary = document.getElementById('categorySummary');
        categorySummary.innerHTML = `
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Total</th>
                            <th class="text-end">% of Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(categoryData).map(([category, amount]) => {
                            const percentage = (amount / Object.values(categoryData).reduce((a, b) => a + b, 0)) * 100;
                            return `
                                <tr>
                                    <td>${category}</td>
                                    <td>${amount.toFixed(2)}</td>
                                    <td class="text-end">${percentage.toFixed(1)}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;

        // Display monthly summary
        const monthlySummary = document.getElementById('monthlySummary');
        monthlySummary.innerHTML = `
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>Total</th>
                            <th class="text-end">Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${monthlyData.map((item, index) => {
                            const prevItem = monthlyData[index + 1];
                            const change = prevItem ? ((item.total - prevItem.total) / prevItem.total * 100).toFixed(1) : 0;
                            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
                            return `
                                <tr>
                                    <td>${item.month}</td>
                                    <td>${item.total.toFixed(2)}</td>
                                    <td class="text-end ${changeClass}">${change}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;

        // Display most expensive expenses
        const mostExpensive = document.getElementById('mostExpensive');
        mostExpensive.innerHTML = `
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Category</th>
                            <th>Paid By</th>
                            <th>Shares</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${expensiveData.map(item => {
                            const shares = item.shares.map(share => 
                                `${share.person}: ${share.type === 'percentage' ? share.value + '%' : share.value}`
                            ).join(', ');
                            return `
                                <tr>
                                    <td>${item.description}</td>
                                    <td>${item.amount.toFixed(2)}</td>
                                    <td>${item.category}</td>
                                    <td>${item.paid_by}</td>
                                    <td>${shares}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error fetching analytics:', error);
        alert('Failed to load analytics. Please try again.');
    }
}

// Handle form submission
document.getElementById('expenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {};
    
    // Convert form data to object
    for (const [key, value] of formData.entries()) {
        if (key.startsWith('share[')) {
            const [shareIndex, field] = key.match(/share\[(\d+)\]\[(.*?)\]/).slice(1);
            if (!data.shares) data.shares = [];
            if (!data.shares[shareIndex]) data.shares[shareIndex] = {};
            data.shares[shareIndex][field] = value;
        } else {
            data[key] = value;
        }
    }

    try {
        const response = await fetch('/api/v1/expenses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            const result = await response.json();
            alert('Expense added successfully!');
            e.target.reset();
            fetchAnalytics(); // Refresh analytics
        } else {
            const error = await response.json();
            alert(error.detail || 'Failed to add expense');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to add expense');
    }
});

// Load analytics when page loads
window.onload = fetchAnalytics;
