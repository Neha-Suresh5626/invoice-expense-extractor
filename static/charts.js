window.onload = function () {

    const ctx = document.getElementById('expenseChart');

    if (!ctx) return;

    const totalExpense = ctx.dataset.total;

    new Chart(ctx, {

        type: 'bar',

        data: {

            labels: ['Total Expense'],

            datasets: [{

                label: 'Expense Amount',

                data: [totalExpense],

                borderWidth: 1

            }]

        },

        options: {

            responsive: true,

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

};