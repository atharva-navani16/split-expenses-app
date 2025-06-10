// Configuration
const API_BASE_URL = window.location.origin + '/api';

// Global variables
let currentExpenses = [];
let currentBalances = [];
let currentSettlements = [];

// DOM Elements
const expenseForm = document.getElementById('expenseForm');
const alertContainer = document.getElementById('alertContainer');
const expensesList = document.getElementById('expensesList');
const balancesList = document.getElementById('balancesList');
const settlementsList = document.getElementById('settlementsList');

// Utility Functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatCurrency(amount) {
    return `₹${parseFloat(amount).toFixed(2)}`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Expense Functions
async function addExpense(expenseData) {
    return await apiCall('/expenses', {
        method: 'POST',
        body: JSON.stringify(expenseData)
    });
}

async function loadExpenses() {
    try {
        expensesList.innerHTML = '<div class="loading">Loading expenses...</div>';
        const response = await apiCall('/expenses');
        currentExpenses = response.data.expenses;
        renderExpenses();
        updateStats();
    } catch (error) {
        expensesList.innerHTML = `<div class="alert alert-error">Error loading expenses: ${error.message}</div>`;
    }
}

async function deleteExpense(expenseId) {
    if (!confirm('Are you sure you want to delete this expense?')) {
        return;
    }

    try {
        await apiCall(`/expenses/${expenseId}`, { method: 'DELETE' });
        showAlert('Expense deleted successfully');
        loadExpenses();
        loadBalances();
        loadSettlements();
    } catch (error) {
        showAlert(`Error deleting expense: ${error.message}`, 'error');
    }
}

function renderExpenses() {
    if (currentExpenses.length === 0) {
        expensesList.innerHTML = `
            <div class="empty-state">
                <h3>No expenses yet</h3>
                <p>Add your first expense above to get started!</p>
            </div>
        `;
        return;
    }

    expensesList.innerHTML = currentExpenses.map(expense => `
        <div class="expense-item">
            <div class="expense-header">
                <div>
                    <div class="expense-amount">${formatCurrency(expense.amount)}</div>
                    <div class="expense-description">${expense.description}</div>
                    <div class="expense-meta">
                        Paid by <strong>${expense.paid_by}</strong> • ${formatDate(expense.created_at)}
                    </div>
                </div>
            </div>
            <div class="expense-actions">
                <button class="btn btn-danger" onclick="deleteExpense('${expense.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

// Balance Functions
async function loadBalances() {
    try {
        balancesList.innerHTML = '<div class="loading">Loading balances...</div>';
        const response = await apiCall('/balances');
        currentBalances = response.data.balances;
        renderBalances();
    } catch (error) {
        balancesList.innerHTML = `<div class="alert alert-error">Error loading balances: ${error.message}</div>`;
    }
}

function renderBalances() {
    if (currentBalances.length === 0) {
        balancesList.innerHTML = `
            <div class="empty-state">
                <h3>No balances yet</h3>
                <p>Add some expenses to see who owes what!</p>
            </div>
        `;
        return;
    }

    balancesList.innerHTML = currentBalances.map(balance => {
        let balanceClass = 'balance-neutral';
        let balanceText = 'Even';
        
        if (balance.balance > 0.01) {
            balanceClass = 'balance-positive';
            balanceText = `Gets ${formatCurrency(balance.balance)}`;
        } else if (balance.balance < -0.01) {
            balanceClass = 'balance-negative';
            balanceText = `Owes ${formatCurrency(Math.abs(balance.balance))}`;
        }

        return `
            <div class="balance-item ${balanceClass}">
                <div>
                    <div class="balance-name">${balance.person}</div>
                    <div class="expense-meta">
                        Paid: ${formatCurrency(balance.total_paid)} • 
                        Share: ${formatCurrency(balance.total_share)}
                    </div>
                </div>
                <div class="balance-amount">${balanceText}</div>
            </div>
        `;
    }).join('');
}

// Settlement Functions
async function loadSettlements() {
    try {
        settlementsList.innerHTML = '<div class="loading">Loading settlements...</div>';
        const response = await apiCall('/settlements');
        currentSettlements = response.data.settlements;
        renderSettlements();
    } catch (error) {
        settlementsList.innerHTML = `<div class="alert alert-error">Error loading settlements: ${error.message}</div>`;
    }
}

function renderSettlements() {
    if (currentSettlements.length === 0) {
        settlementsList.innerHTML = `
            <div class="empty-state">
                <h3>All settled up! 🎉</h3>
                <p>No payments needed right now.</p>
            </div>
        `;
        return;
    }

    settlementsList.innerHTML = currentSettlements.map(settlement => `
        <div class="settlement-item">
            <div class="settlement-text">
                <strong>${settlement.from_person}</strong> should pay <strong>${settlement.to_person}</strong>
            </div>
            <div class="settlement-amount">${formatCurrency(settlement.amount)}</div>
        </div>
    `).join('');
}

// Stats Functions
function updateStats() {
    const totalExpenses = currentExpenses.length;
    const totalAmount = currentExpenses.reduce((sum, exp) => sum + exp.amount, 0);
    const uniquePeople = [...new Set(currentExpenses.map(exp => exp.paid_by))];
    const totalPeople = uniquePeople.length;
    const pendingSettlements = currentSettlements.length;

    document.getElementById('totalExpenses').textContent = totalExpenses;
    document.getElementById('totalAmount').textContent = formatCurrency(totalAmount);
    document.getElementById('totalPeople').textContent = totalPeople;
    document.getElementById('pendingSettlements').textContent = pendingSettlements;
}

// Event Handlers
expenseForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const amount = parseFloat(document.getElementById('amount').value);
    const description = document.getElementById('description').value.trim();
    const paidBy = document.getElementById('paidBy').value.trim();

    const expenseData = {
        amount: amount,
        description: description,
        paid_by: paidBy
    };

    // Client-side validation
    if (expenseData.amount <= 0) {
        showAlert('Amount must be positive', 'error');
        return;
    }

    if (!expenseData.description) {
        showAlert('Description is required', 'error');
        return;
    }

    if (!expenseData.paid_by) {
        showAlert('Paid by is required', 'error');
        return;
    }

    try {
        await addExpense(expenseData);
        showAlert('Expense added successfully!');
        expenseForm.reset();
        
        // Reload all data
        await Promise.all([
            loadExpenses(),
            loadBalances(),
            loadSettlements()
        ]);
    } catch (error) {
        showAlert(`Error adding expense: ${error.message}`, 'error');
    }
});

// Initialize the app
async function initApp() {
    try {
        // Test API connection
        await apiCall('/');
        showAlert('Connected to Split App API successfully!');
        
        // Load initial data
        await Promise.all([
            loadExpenses(),
            loadBalances(),
            loadSettlements()
        ]);
    } catch (error) {
        showAlert(`Failed to connect to API: ${error.message}. Please check if the backend is running.`, 'error');
    }
}

// Start the app when page loads
document.addEventListener('DOMContentLoaded', initApp);

// Auto-refresh data every 30 seconds
setInterval(async () => {
    try {
        await Promise.all([
            loadExpenses(),
            loadBalances(),
            loadSettlements()
        ]);
    } catch (error) {
        console.warn('Auto-refresh failed:', error);
    }
}, 30000);