document.addEventListener("DOMContentLoaded", function() {
    const pieConfig = {
        type: 'doughnut',
        data: {
            datasets: [
                {
                    data: [{{ rest }}, {{ solde_depense_abs }}],
                    /**
                     * These colors come from Tailwind CSS palette
                     * https://tailwindcss.com/docs/customizing-colors/#default-color-palette
                     */
                    backgroundColor: ['#fcba03', '#fc1c03'],
                    label: 'Dataset 1',
                },
            ],
            labels: ['Rest de Budget', 'les dépenses'],
        },
        options: {
            responsive: true,
            cutoutPercentage: 80,
            legend: {
                display: false,
            },
        },
    };
  
    // change this to the id of your chart element in HTML
    const pieCtx = document.getElementById('pie');
    window.myPie = new Chart(pieCtx, pieConfig);
});