document.addEventListener("DOMContentLoaded", function() {
  const budget = {{ budget|default_if_none:"0" }};
  const soldeDepense = {{ solde_depense|default_if_none:"0" }};
  const rest = {{ rest|default_if_none:"0" }};

  const pieConfig = {
      type: 'doughnut',
      data: {
          datasets: [
              {
                  data: [rest, soldeDepense],
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
  }

  const pieCtx = document.getElementById('pie');
  window.myPie = new Chart(pieCtx, pieConfig);
});
