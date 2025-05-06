const labels = window.chartData.labels;
const values = window.chartData.values;
// Premier graphique - Doughnut
const ctx = document.getElementById('expensesChart').getContext('2d');
const expensesChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: labels,
        datasets: [{
            label: "Dépenses (Ar)",
            data: values,
            backgroundColor: [
                "rgba(255, 99, 132, 0.7)",
                "rgba(54, 162, 235, 0.7)",
                "rgba(255, 206, 86, 0.7)",
                "rgba(75, 192, 192, 0.7)",
                "rgba(153, 102, 255, 0.7)"
            ],
            borderColor: "rgba(255, 255, 255, 1)",
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
            },
        }
    }
});

// Deuxième graphique - Area Chart (courbe remplie)
const ctx2 = document.getElementById('monthlyChart').getContext('2d');
const monthlyChart = new Chart(ctx2, {
    type: 'line',
    data: {
        labels: ["Janvier", "Février", "Mars", "Avril"],
        datasets: [{
            label: "Total Dépenses par Mois (Ar)",
            data: [500000, 700000, 400000, 600000],
            fill: true,
            backgroundColor: "rgba(75, 192, 192, 0.2)", // Zone sous la ligne
            borderColor: "rgba(75, 192, 192, 1)", // Couleur de la ligne
            tension: 0.4, // Douceur de la courbe
            pointBackgroundColor: "rgba(75, 192, 192, 1)", // Couleur des points
            pointBorderColor: "#fff", // Bordure blanche des points
            pointHoverRadius: 6 // Grossir au survol
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: "#333", // Couleur du texte de la légende
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.formattedValue + ' Ar';
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString('fr-FR') + ' Ar';
                    },
                    color: "#666" // Couleur du texte sur l'axe Y
                }
            },
            x: {
                ticks: {
                    color: "#666" // Couleur du texte sur l'axe X
                }
            }
        }
    }
});



document.addEventListener("DOMContentLoaded", function () {
  const deleteForms = document.querySelectorAll(".delete-form");

  deleteForms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault(); // Empêcher la soumission immédiate

      Swal.fire({
        title: "Êtes-vous sûr ?",
        text: "Cette action est irréversible !",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#d33",
        confirmButtonText: "Oui, supprimer !",
        cancelButtonText: "Non, annuler",
      }).then((result) => {
        if (result.isConfirmed) {
          form.submit();
        }
      });
    });
  });
});
