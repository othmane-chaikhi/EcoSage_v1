document.addEventListener("DOMContentLoaded", function() {
    const piee = document.getElementById('piee');
    const rest = piee.getAttribute('data-rest');
    const soldeDepenseAbs = piee.getAttribute('data-solde-depense-abs');
    
    const pieConfig = {
        type: 'doughnut',
        data: {
            datasets: [
                {
                    data: [rest, soldeDepenseAbs], // Use the variables directly
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
  
    // Change this to the id of your chart element in HTML
    const pieCtx = document.getElementById('pie');
    window.myPie = new Chart(pieCtx, pieConfig);
});
